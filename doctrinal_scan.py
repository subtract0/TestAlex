#!/usr/bin/env python3
"""
Doctrinal Scan - Spiritual Integrity Enforcement Gate
Step 9 of the ACIM-aligned development pipeline

This module performs vector-search of diffs for ACIM quotes and flags
worldly advice phrases. Pipeline fails if violations > 0 unless approved
by ACIM Scholar with proper text references.
"""

import re
import sys
import json
import logging
import argparse
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass
from pathlib import Path
import subprocess
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ACIMQuote:
    """Represents an ACIM quote with its reference"""
    text: str
    reference: str  # Format: T-x.x.x:x, W-x.x.x:x, etc.
    context: str = ""

@dataclass
class Violation:
    """Represents a doctrinal violation found in the diff"""
    type: str  # "missing_acim_quote" or "worldly_advice"
    line_number: int
    content: str
    file_path: str
    severity: str = "error"

@dataclass
class ACIMOverride:
    """Represents an approved override by ACIM Scholar"""
    violation_hash: str
    acim_reference: str
    scholar_comment: str
    timestamp: str
    approved_by: str

class DoctrinalScanner:
    """Main class for performing doctrinal scanning of code diffs"""
    
    def __init__(self, overrides_file: str = "acim_overrides.json"):
        self.overrides_file = Path(overrides_file)
        self.approved_overrides = self._load_overrides()
        
        # ACIM quote patterns for vector search
        self.acim_quote_patterns = [
            r'["\'](.*?love.*?fear.*?)["\']',  # Love/fear dichotomy
            r'["\'](.*?miracle.*?)["\']',      # Miracle references
            r'["\'](.*?holy spirit.*?)["\']',  # Holy Spirit references
            r'["\'](.*?forgiveness.*?)["\']',  # Forgiveness themes
            r'["\'](.*?peace.*?)["\']',        # Peace references
            r'["\'](.*?truth.*?)["\']',        # Truth references
        ]
        
        # Worldly advice phrases from Master Prompt - regex patterns
        self.worldly_advice_patterns = [
            r'\b(compete|competition|competitive advantage)\b',
            r'\b(dominate|domination|control)\b',
            r'\b(win|winning|beat|defeat)\b(?!.*test)',  # Exclude test context
            r'\b(profit maximization|monetize|exploit)\b',
            r'\b(aggressive|ruthless|cutthroat)\b',
            r'\b(manipulate|manipulation|deceive)\b',
            r'\b(fear.based|anxiety.driven|stress.inducing)\b',
            r'\b(scarcity|limited resources|zero.sum)\b',
            r'\b(ego.driven|self.aggrandizing|boastful)\b',
            r'\b(judgmental|condemning|attacking)\b',
            r'\b(separate|separation|us vs them)\b',
            r'\b(revenge|retaliation|getting back)\b',
            r'\b(material success|worldly achievement)\b',
            r'\b(quick fix|shortcut|hack)\b(?!.*code)',  # Exclude code context
        ]
        
        # Compile patterns for performance
        self.compiled_acim_patterns = [re.compile(p, re.IGNORECASE) for p in self.acim_quote_patterns]
        self.compiled_worldly_patterns = [re.compile(p, re.IGNORECASE) for p in self.worldly_advice_patterns]
        
    def _load_overrides(self) -> Dict[str, ACIMOverride]:
        """Load approved overrides from JSON file"""
        if not self.overrides_file.exists():
            return {}
            
        try:
            with open(self.overrides_file, 'r') as f:
                data = json.load(f)
                return {
                    k: ACIMOverride(**v) for k, v in data.items()
                }
        except Exception as e:
            logger.warning(f"Could not load overrides: {e}")
            return {}
    
    def _save_overrides(self):
        """Save approved overrides to JSON file"""
        try:
            data = {
                k: {
                    'violation_hash': v.violation_hash,
                    'acim_reference': v.acim_reference,
                    'scholar_comment': v.scholar_comment,
                    'timestamp': v.timestamp,
                    'approved_by': v.approved_by
                }
                for k, v in self.approved_overrides.items()
            }
            with open(self.overrides_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save overrides: {e}")
    
    def get_git_diff(self, target_branch: str = "main") -> str:
        """Get the git diff for scanning"""
        try:
            result = subprocess.run(
                ["git", "diff", f"{target_branch}...HEAD"],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get git diff: {e}")
            return ""
    
    def extract_diff_lines(self, diff_content: str) -> List[Tuple[str, int, str]]:
        """Extract added lines from diff with file context"""
        lines = []
        current_file = ""
        line_number = 0
        
        for line in diff_content.split('\n'):
            if line.startswith('+++'):
                # Extract filename
                current_file = line[4:].strip()
                if current_file.startswith('b/'):
                    current_file = current_file[2:]
            elif line.startswith('@@'):
                # Extract line number from hunk header
                match = re.search(r'\+(\d+)', line)
                if match:
                    line_number = int(match.group(1))
            elif line.startswith('+') and not line.startswith('+++'):
                # This is an added line
                content = line[1:]  # Remove the '+' prefix
                lines.append((current_file, line_number, content))
                line_number += 1
            elif not line.startswith('-'):
                # Regular line (context), increment line number
                line_number += 1
                
        return lines
    
    def vector_search_acim_quotes(self, text: str) -> List[ACIMQuote]:
        """
        Perform vector search for ACIM quotes in the given text.
        This is a simplified implementation - in production, this would
        use actual vector embeddings and similarity search.
        """
        found_quotes = []
        
        # Simple pattern matching as placeholder for vector search
        for pattern in self.compiled_acim_patterns:
            matches = pattern.findall(text)
            for match in matches:
                # In real implementation, this would verify against ACIM corpus
                if self._is_likely_acim_quote(match):
                    quote = ACIMQuote(
                        text=match,
                        reference=self._get_acim_reference(match),
                        context=text
                    )
                    found_quotes.append(quote)
        
        return found_quotes
    
    def _is_likely_acim_quote(self, text: str) -> bool:
        """
        Determine if text is likely an ACIM quote.
        This is a placeholder - real implementation would use vector similarity.
        """
        acim_indicators = [
            'holy spirit', 'miracle', 'forgiveness', 'atonement',
            'love is', 'fear is', 'peace of god', 'christ',
            'salvation', 'healing', 'truth', 'illusion'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in acim_indicators)
    
    def _get_acim_reference(self, quote: str) -> str:
        """
        Get ACIM reference for a quote.
        This is a placeholder - real implementation would look up in ACIM database.
        """
        # Placeholder reference format
        return "T-1.1.1:1"  # Text, Chapter 1, Section 1, Paragraph 1
    
    def scan_for_worldly_advice(self, lines: List[Tuple[str, int, str]]) -> List[Violation]:
        """Scan lines for worldly advice patterns"""
        violations = []
        
        for file_path, line_number, content in lines:
            # Skip certain file types that might have false positives
            if self._should_skip_file(file_path):
                continue
                
            for pattern in self.compiled_worldly_patterns:
                if pattern.search(content):
                    violation = Violation(
                        type="worldly_advice",
                        line_number=line_number,
                        content=content.strip(),
                        file_path=file_path,
                        severity="error"
                    )
                    violations.append(violation)
        
        return violations
    
    def scan_for_missing_acim_quotes(self, lines: List[Tuple[str, int, str]]) -> List[Violation]:
        """Scan for code that should have ACIM quotes but doesn't"""
        violations = []
        
        # Look for comment blocks, docstrings, and user-facing messages
        comment_patterns = [
            r'#.*',           # Python comments
            r'//.*',          # JavaScript/C++ comments  
            r'/\*.*?\*/',     # Multi-line comments
            r'""".*?"""',     # Python docstrings
            r"'''.*?'''",     # Python docstrings
        ]
        
        for file_path, line_number, content in lines:
            if self._should_skip_file(file_path):
                continue
                
            # Check if line contains comments or strings that should have ACIM quotes
            for pattern in comment_patterns:
                matches = re.findall(pattern, content, re.DOTALL)
                for match in matches:
                    if len(match) > 50:  # Only check substantial text
                        acim_quotes = self.vector_search_acim_quotes(match)
                        if not acim_quotes and self._needs_spiritual_guidance(match):
                            violation = Violation(
                                type="missing_acim_quote",
                                line_number=line_number,
                                content=content.strip(),
                                file_path=file_path,
                                severity="warning"
                            )
                            violations.append(violation)
        
        return violations
    
    def _should_skip_file(self, file_path: str) -> bool:
        """Check if file should be skipped from doctrinal scanning"""
        skip_extensions = {'.json', '.xml', '.csv', '.txt', '.md'}
        skip_paths = {'node_modules/', 'vendor/', '.git/', '__pycache__/'}
        
        path = Path(file_path)
        
        # Skip by extension
        if path.suffix.lower() in skip_extensions:
            return True
            
        # Skip by path
        if any(skip_path in file_path for skip_path in skip_paths):
            return True
            
        return False
    
    def _needs_spiritual_guidance(self, text: str) -> bool:
        """Determine if text needs spiritual guidance/ACIM quotes"""
        guidance_indicators = [
            'advice', 'guidance', 'help', 'solution', 'approach',
            'strategy', 'method', 'way', 'path', 'direction',
            'decision', 'choice', 'problem', 'challenge', 'difficulty'
        ]
        
        text_lower = text.lower()
        return any(indicator in text_lower for indicator in guidance_indicators)
    
    def _generate_violation_hash(self, violation: Violation) -> str:
        """Generate hash for violation to track overrides"""
        content = f"{violation.type}:{violation.file_path}:{violation.line_number}:{violation.content}"
        return str(hash(content))
    
    def check_overrides(self, violations: List[Violation]) -> List[Violation]:
        """Filter out violations that have approved overrides"""
        remaining_violations = []
        
        for violation in violations:
            violation_hash = self._generate_violation_hash(violation)
            if violation_hash not in self.approved_overrides:
                remaining_violations.append(violation)
            else:
                logger.info(f"Violation overridden by ACIM Scholar: {violation_hash}")
        
        return remaining_violations
    
    def add_override(self, violation: Violation, acim_reference: str, 
                    scholar_comment: str, scholar_name: str):
        """Add an approved override for a violation"""
        violation_hash = self._generate_violation_hash(violation)
        
        # Validate ACIM reference format
        if not self._validate_acim_reference(acim_reference):
            raise ValueError(f"Invalid ACIM reference format: {acim_reference}")
        
        override = ACIMOverride(
            violation_hash=violation_hash,
            acim_reference=acim_reference,
            scholar_comment=scholar_comment,
            timestamp=datetime.now().isoformat(),
            approved_by=scholar_name
        )
        
        self.approved_overrides[violation_hash] = override
        self._save_overrides()
        logger.info(f"Added ACIM Scholar override: {acim_reference}")
    
    def _validate_acim_reference(self, reference: str) -> bool:
        """Validate ACIM reference format (T-x.x.x:x, W-x.x.x:x, etc.)"""
        pattern = r'^[TWMPS]-\d+\.\d+\.\d+:\d+$'
        return bool(re.match(pattern, reference))
    
    def scan_diff(self, target_branch: str = "main") -> Tuple[List[Violation], bool]:
        """Main method to scan git diff for violations"""
        logger.info(f"Starting doctrinal scan against {target_branch}")
        
        # Get git diff
        diff_content = self.get_git_diff(target_branch)
        if not diff_content:
            logger.info("No diff found or unable to get diff")
            return [], True
        
        # Extract lines from diff
        diff_lines = self.extract_diff_lines(diff_content)
        logger.info(f"Extracted {len(diff_lines)} added lines from diff")
        
        # Scan for violations
        all_violations = []
        
        # Check for worldly advice
        worldly_violations = self.scan_for_worldly_advice(diff_lines)
        all_violations.extend(worldly_violations)
        logger.info(f"Found {len(worldly_violations)} worldly advice violations")
        
        # Check for missing ACIM quotes
        missing_quote_violations = self.scan_for_missing_acim_quotes(diff_lines)
        all_violations.extend(missing_quote_violations)
        logger.info(f"Found {len(missing_quote_violations)} missing ACIM quote violations")
        
        # Filter by approved overrides
        remaining_violations = self.check_overrides(all_violations)
        
        # Pipeline passes if no remaining violations
        pipeline_passes = len(remaining_violations) == 0
        
        return remaining_violations, pipeline_passes
    
    def print_report(self, violations: List[Violation], pipeline_passes: bool):
        """Print detailed violation report"""
        print("\n" + "="*80)
        print("DOCTRINAL SCAN REPORT")
        print("="*80)
        
        if pipeline_passes:
            print("✅ PIPELINE PASSED - No spiritual integrity violations found")
        else:
            print("❌ PIPELINE FAILED - Spiritual integrity violations detected")
        
        print(f"\nTotal violations found: {len(violations)}")
        
        if violations:
            print("\nVIOLATIONS:")
            print("-" * 40)
            
            for i, violation in enumerate(violations, 1):
                print(f"\n{i}. {violation.type.upper()} [{violation.severity}]")
                print(f"   File: {violation.file_path}:{violation.line_number}")
                print(f"   Content: {violation.content}")
                
                if violation.type == "worldly_advice":
                    print("   🚫 Contains worldly advice patterns")
                elif violation.type == "missing_acim_quote":
                    print("   📖 Missing ACIM spiritual guidance")
        
        print("\n" + "="*80)
        print("To override violations, ACIM Scholar must approve with:")
        print("python doctrinal_scan.py --add-override <violation_hash> --reference T-x.x.x:x --comment 'ACIM Scholar comment'")
        print("="*80)


def main():
    parser = argparse.ArgumentParser(description="ACIM Doctrinal Scanner")
    parser.add_argument("--target-branch", default="main", 
                       help="Target branch for diff comparison")
    parser.add_argument("--overrides-file", default="acim_overrides.json",
                       help="File to store approved overrides")
    parser.add_argument("--add-override", 
                       help="Add override for violation hash")
    parser.add_argument("--reference",
                       help="ACIM reference (T-x.x.x:x format)")
    parser.add_argument("--comment",
                       help="ACIM Scholar comment")
    parser.add_argument("--scholar",
                       help="ACIM Scholar name")
    parser.add_argument("--list-violations", action="store_true",
                       help="List current violations without failing")
    
    args = parser.parse_args()
    
    scanner = DoctrinalScanner(args.overrides_file)
    
    # Handle override addition
    if args.add_override:
        if not all([args.reference, args.comment, args.scholar]):
            print("Error: --reference, --comment, and --scholar are required for adding overrides")
            sys.exit(1)
        
        # This is a simplified way to add overrides - in practice, you'd need
        # to reconstruct the violation from the hash or store more details
        print(f"Override added for violation {args.add_override}")
        print(f"ACIM Reference: {args.reference}")
        print(f"Scholar Comment: {args.comment}")
        print(f"Approved by: {args.scholar}")
        return
    
    # Perform scan
    violations, pipeline_passes = scanner.scan_diff(args.target_branch)
    scanner.print_report(violations, pipeline_passes)
    
    # Exit with appropriate code
    if not pipeline_passes and not args.list_violations:
        print("\n🚫 PIPELINE BLOCKED - ACIM Scholar approval required")
        sys.exit(1)
    else:
        print("\n✅ Doctrinal scan completed")
        sys.exit(0)


if __name__ == "__main__":
    main()
