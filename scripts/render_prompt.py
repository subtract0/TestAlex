#!/usr/bin/env python3
"""
Autonomous Agent Prompt System Renderer

This script concatenates master system prompt, role-specific prompts, and
snippet components to create complete prompts for runtime consumption by
autonomous agents.

Usage:
    python scripts/render_prompt.py --role backend_engineer --output rendered.txt
    python scripts/render_prompt.py --role android_engineer --snippets guardrails security_performance
    python scripts/render_prompt.py --validate-all
"""

import argparse
import logging
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class PromptValidationResult:
    """Result of prompt validation checks"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    file_path: str


@dataclass
class PromptComponent:
    """Represents a single prompt component (master, role, or snippet)"""
    name: str
    path: Path
    content: str
    type: str  # 'master', 'role', 'snippet'


class PromptRenderer:
    """
    Renders complete prompts by concatenating master prompt, role prompts,
    and modular snippets while maintaining ACIM fidelity and technical standards.
    """
    
    def __init__(self, prompts_dir: Optional[Path] = None):
        """
        Initialize the prompt renderer.
        
        Args:
            prompts_dir: Path to the prompts directory. Defaults to repository root/prompts.
        """
        if prompts_dir is None:
            # Assume script is in scripts/ directory, prompts are in ../prompts/
            script_dir = Path(__file__).parent
            self.prompts_dir = script_dir.parent / "prompts"
        else:
            self.prompts_dir = Path(prompts_dir)
            
        if not self.prompts_dir.exists():
            raise FileNotFoundError(f"Prompts directory not found: {self.prompts_dir}")
            
        self.snippets_dir = self.prompts_dir / "snippets"
        
        # Cache for loaded prompts to avoid re-reading files
        self._prompt_cache: Dict[str, PromptComponent] = {}
        
        # Known roles (can be extended)
        self.available_roles = self._discover_available_roles()
        self.available_snippets = self._discover_available_snippets()
        
        logger.info(f"Initialized PromptRenderer with {len(self.available_roles)} roles "
                   f"and {len(self.available_snippets)} snippets")
    
    def _discover_available_roles(self) -> Set[str]:
        """Discover available role prompts by scanning the prompts directory"""
        roles = set()
        
        # Look for files matching pattern [role]_engineer.md or specific role names
        role_patterns = [
            r"(\w+)_engineer\.md$",  # backend_engineer.md, android_engineer.md, etc.
            r"(devops_sre)\.md$",    # devops_sre.md
            r"(qa_tester)\.md$",     # qa_tester.md
            r"(acim_scholar)\.md$"   # acim_scholar.md
        ]
        
        for file_path in self.prompts_dir.glob("*.md"):
            if file_path.name in ["master_system_prompt.md", "orchestration_protocol.md"]:
                continue  # Skip non-role files
                
            for pattern in role_patterns:
                match = re.match(pattern, file_path.name)
                if match:
                    roles.add(match.group(1))
                    break
                    
        return roles
    
    def _discover_available_snippets(self) -> Set[str]:
        """Discover available snippet components"""
        if not self.snippets_dir.exists():
            return set()
            
        snippets = set()
        for file_path in self.snippets_dir.glob("*.md"):
            snippet_name = file_path.stem
            snippets.add(snippet_name)
            
        return snippets
    
    def _load_prompt_component(self, name: str, component_type: str) -> PromptComponent:
        """Load a prompt component from disk with caching"""
        cache_key = f"{component_type}:{name}"
        
        if cache_key in self._prompt_cache:
            return self._prompt_cache[cache_key]
        
        if component_type == "master":
            file_path = self.prompts_dir / "master_system_prompt.md"
        elif component_type == "orchestration":
            file_path = self.prompts_dir / "orchestration_protocol.md"
        elif component_type == "role":
            # Try different naming patterns for roles
            possible_names = [
                f"{name}_engineer.md",
                f"{name}.md"
            ]
            
            file_path = None
            for possible_name in possible_names:
                candidate_path = self.prompts_dir / possible_name
                if candidate_path.exists():
                    file_path = candidate_path
                    break
                    
            if file_path is None:
                raise FileNotFoundError(f"Role prompt not found for: {name}")
                
        elif component_type == "snippet":
            file_path = self.snippets_dir / f"{name}.md"
        else:
            raise ValueError(f"Unknown component type: {component_type}")
        
        if not file_path.exists():
            raise FileNotFoundError(f"Prompt component not found: {file_path}")
        
        try:
            content = file_path.read_text(encoding='utf-8')
            component = PromptComponent(
                name=name,
                path=file_path,
                content=content,
                type=component_type
            )
            
            self._prompt_cache[cache_key] = component
            return component
            
        except Exception as e:
            raise IOError(f"Failed to load prompt component {file_path}: {e}")
    
    def render_role_prompt(self, role: str, snippets: Optional[List[str]] = None, 
                          include_orchestration: bool = False) -> str:
        """
        Render a complete prompt for a specific role.
        
        Args:
            role: The role to render (e.g., 'backend_engineer', 'android_engineer')
            snippets: Optional list of snippet names to include
            include_orchestration: Whether to include orchestration protocol
            
        Returns:
            Complete rendered prompt as a string
            
        Raises:
            FileNotFoundError: If role or snippet files don't exist
            ValueError: If role is not recognized
        """
        if role not in self.available_roles:
            raise ValueError(f"Unknown role: {role}. Available roles: {sorted(self.available_roles)}")
        
        if snippets is None:
            snippets = []
        
        # Validate snippets
        invalid_snippets = set(snippets) - self.available_snippets
        if invalid_snippets:
            raise ValueError(f"Unknown snippets: {sorted(invalid_snippets)}. "
                           f"Available snippets: {sorted(self.available_snippets)}")
        
        logger.info(f"Rendering prompt for role '{role}' with snippets: {snippets}")
        
        # Load components
        try:
            master_prompt = self._load_prompt_component("master", "master")
            role_prompt = self._load_prompt_component(role, "role")
            
            snippet_prompts = []
            for snippet_name in snippets:
                snippet_prompts.append(self._load_prompt_component(snippet_name, "snippet"))
            
            orchestration_prompt = None
            if include_orchestration:
                orchestration_prompt = self._load_prompt_component("orchestration", "orchestration")
                
        except FileNotFoundError as e:
            logger.error(f"Failed to load prompt components: {e}")
            raise
        
        # Render the complete prompt
        rendered_parts = [
            "# AUTONOMOUS AGENT PROMPT SYSTEM",
            "# Generated by scripts/render_prompt.py",
            f"# Role: {role}",
            f"# Snippets: {', '.join(snippets) if snippets else 'None'}",
            f"# Generated at: {self._get_timestamp()}",
            "",
            "# " + "=" * 80,
            "# MASTER SYSTEM PROMPT",
            "# " + "=" * 80,
            "",
            master_prompt.content,
            ""
        ]
        
        if orchestration_prompt:
            rendered_parts.extend([
                "# " + "=" * 80,
                "# ORCHESTRATION PROTOCOL", 
                "# " + "=" * 80,
                "",
                orchestration_prompt.content,
                ""
            ])
        
        rendered_parts.extend([
            "# " + "=" * 80,
            f"# ROLE-SPECIFIC PROMPT: {role.upper().replace('_', ' ')}",
            "# " + "=" * 80,
            "",
            role_prompt.content,
            ""
        ])
        
        # Add snippets
        for snippet_prompt in snippet_prompts:
            rendered_parts.extend([
                "# " + "=" * 80,
                f"# SNIPPET: {snippet_prompt.name.upper().replace('_', ' ')}",
                "# " + "=" * 80,
                "",
                snippet_prompt.content,
                ""
            ])
        
        # Final assembly instructions
        rendered_parts.extend([
            "# " + "=" * 80,
            "# INTEGRATION INSTRUCTIONS",
            "# " + "=" * 80,
            "",
            "You are now equipped with the complete prompt system for the ACIMguide project.",
            "Your responses must adhere to ALL of the above principles, rules, and protocols.",
            "",
            "Key reminders:",
            "- Maintain absolute ACIM text fidelity in all operations",
            "- Follow the specified coding standards and architecture patterns", 
            "- Respect the spiritual mission and principles of the project",
            "- Apply the appropriate hand-off protocols when coordinating with other agents",
            "- Validate all outputs against the quality and compliance standards defined above",
            "",
            "Begin your specialized agent role now."
        ])
        
        return "\n".join(rendered_parts)
    
    def validate_prompt_component(self, component: PromptComponent) -> PromptValidationResult:
        """
        Validate a single prompt component for completeness and integrity.
        
        Args:
            component: The prompt component to validate
            
        Returns:
            PromptValidationResult with validation details
        """
        errors = []
        warnings = []
        
        content = component.content
        
        # Check for basic structure
        if len(content.strip()) < 100:
            errors.append("Prompt content is suspiciously short (< 100 characters)")
        
        # Check for required sections based on component type
        if component.type == "master":
            required_sections = [
                "Project Vision",
                "High-Level Architecture",
                "Core Doctrinal Rules",
                "Global Coding Commandments",
                "Prohibited Actions"
            ]
        elif component.type == "role":
            required_sections = [
                "Role-Specific Scope",
                "Primary Responsibilities", 
                "Success Criteria",
                "Hand-off Protocols"
            ]
            
            # Check for inheritance from master prompt
            if "Inherits all principles, rules, and architecture from" not in content:
                errors.append("Role prompt missing inheritance declaration from master prompt")
        elif component.type == "snippet":
            required_sections = []  # Snippets are more flexible
        else:
            required_sections = []
        
        # Validate required sections exist
        for section in required_sections:
            if section not in content:
                errors.append(f"Missing required section: '{section}'")
        
        # Check for ACIM-specific content (if applicable)
        if component.type in ["master", "role"]:
            acim_indicators = [
                "ACIM", "Course in Miracles", "spiritual", "Course text",
                "doctrinal", "theological"
            ]
            has_acim_content = any(indicator in content for indicator in acim_indicators)
            if not has_acim_content:
                warnings.append("No ACIM-specific content detected")
        
        # Check for code examples formatting
        code_blocks = re.findall(r'```(\w+)?\n(.*?)```', content, re.DOTALL)
        for i, (lang, code) in enumerate(code_blocks):
            if lang and lang not in ['python', 'javascript', 'typescript', 'kotlin', 'java', 'yaml', 'json', 'bash']:
                warnings.append(f"Code block {i+1} uses unrecognized language: {lang}")
            
            # Check for obviously broken code (basic syntax)
            if lang == 'python' and code.strip():
                # Very basic Python syntax check
                if code.count('(') != code.count(')'):
                    warnings.append(f"Python code block {i+1} has unmatched parentheses")
                if code.count('{') != code.count('}'):
                    warnings.append(f"Python code block {i+1} has unmatched braces")
        
        # Check for broken internal links
        internal_links = re.findall(r'\[([^\]]+)\]\(\.\/([^)]+)\)', content)
        for link_text, link_path in internal_links:
            full_path = component.path.parent / link_path
            if not full_path.exists():
                errors.append(f"Broken internal link: {link_path}")
        
        return PromptValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            file_path=str(component.path)
        )
    
    def validate_all_prompts(self) -> List[PromptValidationResult]:
        """
        Validate all prompt components in the system.
        
        Returns:
            List of validation results for all components
        """
        results = []
        
        logger.info("Validating all prompt components...")
        
        # Validate master prompt
        try:
            master_component = self._load_prompt_component("master", "master")
            results.append(self.validate_prompt_component(master_component))
        except Exception as e:
            results.append(PromptValidationResult(
                is_valid=False,
                errors=[f"Failed to load master prompt: {e}"],
                warnings=[],
                file_path="prompts/master_system_prompt.md"
            ))
        
        # Validate orchestration protocol
        try:
            orch_component = self._load_prompt_component("orchestration", "orchestration")
            results.append(self.validate_prompt_component(orch_component))
        except Exception as e:
            results.append(PromptValidationResult(
                is_valid=False,
                errors=[f"Failed to load orchestration protocol: {e}"],
                warnings=[],
                file_path="prompts/orchestration_protocol.md"
            ))
        
        # Validate all role prompts
        for role in sorted(self.available_roles):
            try:
                role_component = self._load_prompt_component(role, "role")
                results.append(self.validate_prompt_component(role_component))
            except Exception as e:
                results.append(PromptValidationResult(
                    is_valid=False,
                    errors=[f"Failed to load role '{role}': {e}"],
                    warnings=[],
                    file_path=f"prompts/{role}*.md"
                ))
        
        # Validate all snippets
        for snippet in sorted(self.available_snippets):
            try:
                snippet_component = self._load_prompt_component(snippet, "snippet")
                results.append(self.validate_prompt_component(snippet_component))
            except Exception as e:
                results.append(PromptValidationResult(
                    is_valid=False,
                    errors=[f"Failed to load snippet '{snippet}': {e}"],
                    warnings=[],
                    file_path=f"prompts/snippets/{snippet}.md"
                ))
        
        return results
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for prompt generation"""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    
    def list_available_components(self) -> Dict[str, List[str]]:
        """List all available prompt components"""
        return {
            "roles": sorted(list(self.available_roles)),
            "snippets": sorted(list(self.available_snippets))
        }


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Render complete prompts for autonomous agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Render a backend engineer prompt
  python scripts/render_prompt.py --role backend_engineer --output backend_prompt.txt
  
  # Include specific snippets
  python scripts/render_prompt.py --role android_engineer --snippets guardrails security_performance
  
  # Validate all prompts
  python scripts/render_prompt.py --validate-all
  
  # List available components
  python scripts/render_prompt.py --list
        """
    )
    
    parser.add_argument(
        "--role",
        help="Role to render prompt for (e.g., backend_engineer, android_engineer)"
    )
    
    parser.add_argument(
        "--snippets",
        nargs="*",
        help="Snippet names to include (e.g., guardrails docs_testing security_performance)"
    )
    
    parser.add_argument(
        "--include-orchestration",
        action="store_true", 
        help="Include orchestration protocol in rendered prompt"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output file path. If not specified, prints to stdout"
    )
    
    parser.add_argument(
        "--validate-all",
        action="store_true",
        help="Validate all prompt components and exit"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available roles and snippets"
    )
    
    parser.add_argument(
        "--prompts-dir",
        help="Path to prompts directory (defaults to repository prompts/ dir)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        renderer = PromptRenderer(args.prompts_dir)
        
        if args.list:
            components = renderer.list_available_components()
            print("Available Components:")
            print(f"  Roles ({len(components['roles'])}): {', '.join(components['roles'])}")
            print(f"  Snippets ({len(components['snippets'])}): {', '.join(components['snippets'])}")
            return 0
        
        if args.validate_all:
            results = renderer.validate_all_prompts()
            
            # Summary
            total_valid = sum(1 for r in results if r.is_valid)
            total_components = len(results)
            
            print(f"Validation Results: {total_valid}/{total_components} components valid")
            print("")
            
            # Detailed results
            has_errors = False
            for result in results:
                status = "✓" if result.is_valid else "✗"
                print(f"{status} {result.file_path}")
                
                if result.errors:
                    has_errors = True
                    for error in result.errors:
                        print(f"  ERROR: {error}")
                        
                if result.warnings:
                    for warning in result.warnings:
                        print(f"  WARNING: {warning}")
                        
                if result.errors or result.warnings:
                    print("")
            
            return 1 if has_errors else 0
        
        if not args.role:
            print("ERROR: --role is required (unless using --validate-all or --list)")
            print("Use --list to see available roles")
            return 1
        
        # Render the prompt
        rendered_prompt = renderer.render_role_prompt(
            role=args.role,
            snippets=args.snippets or [],
            include_orchestration=args.include_orchestration
        )
        
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(rendered_prompt, encoding='utf-8')
            logger.info(f"Rendered prompt written to: {output_path}")
        else:
            print(rendered_prompt)
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to render prompt: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
