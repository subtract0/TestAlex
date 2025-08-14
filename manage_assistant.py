#!/usr/bin/env python3
"""
ACIMguide Assistant Management Script

Consolidated script to create, update, and manage OpenAI assistants for the ACIMguide project.
Replaces setup_assistant.py and update_assistant.py with a more robust, feature-complete solution.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from typing import List, Optional
import openai
from dotenv import load_dotenv, set_key

# Load environment variables
load_dotenv()

# Configure logging
def setup_logging(verbose: bool = False):
    """Configure structured logging for the application."""
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    if verbose:
        log_level = 'DEBUG'
    
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

# Configuration
DEFAULT_FILE_PATHS = [
    "data/A_Course_In_Miracles_Urtext.pdf",
    "data/cleaned_training_data_1.py", 
    "data/cleaned_training_data_2.py",
    "data/cleaned_training_data_3.py"
]

def load_system_prompt():
    """Load system prompt from CourseGPT.md file."""
    try:
        with open("data/CourseGPT.md", "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        raise FileNotFoundError("CourseGPT.md not found. This file is required as the system prompt source.")
    except Exception as e:
        raise Exception(f"Error loading system prompt from CourseGPT.md: {e}")

# Load system prompt from CourseGPT.md (single source of truth)
SYSTEM_PROMPT = load_system_prompt()


class AssistantManager:
    """Manages OpenAI Assistant operations for the ACIMguide project."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.assistant_id = os.getenv("ASSISTANT_ID")
        self.vector_store_id = os.getenv("VECTOR_STORE_ID")
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        try:
            self.client = openai.OpenAI(api_key=self.api_key)
            self.logger.info("OpenAI client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {e}")
            raise

    def validate_files(self, file_paths: List[str]) -> List[str]:
        """Validate that all specified files exist and are readable."""
        valid_paths = []
        for path in file_paths:
            if Path(path).exists():
                valid_paths.append(path)
                self.logger.debug(f"File found: {path}")
            else:
                self.logger.warning(f"File not found: {path}")
        
        if not valid_paths:
            raise FileNotFoundError("No valid files found for upload")
        
        self.logger.info(f"Validated {len(valid_paths)} out of {len(file_paths)} files")
        return valid_paths

    def create_vector_store(self, name: str = "ACIM Knowledge Base") -> str:
        """Create a new vector store for file storage."""
        try:
            self.logger.info(f"Creating vector store: {name}")
            vector_store = self.client.vector_stores.create(name=name)
            self.logger.info(f"Vector store created with ID: {vector_store.id}")
            return vector_store.id
        except openai.APIError as e:
            self.logger.error(f"OpenAI API error creating vector store: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error creating vector store: {e}")
            raise

    def upload_files_to_vector_store(self, vector_store_id: str, file_paths: List[str]) -> None:
        """Upload files to the specified vector store."""
        valid_paths = self.validate_files(file_paths)
        file_streams = []
        
        try:
            self.logger.info(f"Opening {len(valid_paths)} files for upload")
            file_streams = [open(path, "rb") for path in valid_paths]
            
            self.logger.info("Uploading files to vector store...")
            file_batch = self.client.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store_id, 
                files=file_streams
            )
            
            self.logger.info(f"File batch upload status: {file_batch.status}")
            self.logger.info(f"File counts: {file_batch.file_counts}")
            
            if file_batch.status != "completed":
                self.logger.warning(f"File batch upload completed with status: {file_batch.status}")
            
        except openai.APIError as e:
            self.logger.error(f"OpenAI API error uploading files: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error uploading files: {e}")
            raise
        finally:
            # Ensure all file streams are closed
            for f in file_streams:
                if not f.closed:
                    f.close()
            self.logger.debug("All file streams closed")

    def create_assistant(self, name: str = "CourseGPT", model: str = "gpt-5-chat-latest", 
                        vector_store_id: str = None) -> str:
        """Create a new assistant with the specified configuration."""
        try:
            self.logger.info(f"Creating assistant: {name} with model: {model}")
            
            tool_resources = {}
            if vector_store_id:
                tool_resources["file_search"] = {"vector_store_ids": [vector_store_id]}
                self.logger.debug(f"Assistant will use vector store: {vector_store_id}")
            
            assistant = self.client.beta.assistants.create(
                name=name,
                instructions=SYSTEM_PROMPT,
                model=model,
                tools=[{"type": "file_search"}] if vector_store_id else [],
                tool_resources=tool_resources
            )
            
            self.logger.info(f"Assistant created successfully with ID: {assistant.id}")
            return assistant.id
            
        except openai.APIError as e:
            self.logger.error(f"OpenAI API error creating assistant: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error creating assistant: {e}")
            raise

    def update_assistant(self, assistant_id: str, **kwargs) -> None:
        """Update an existing assistant with new parameters."""
        try:
            self.logger.info(f"Updating assistant {assistant_id} with parameters: {kwargs}")
            
            assistant = self.client.beta.assistants.update(assistant_id, **kwargs)
            self.logger.info(f"Assistant updated successfully. Current model: {assistant.model}")
            
        except openai.APIError as e:
            self.logger.error(f"OpenAI API error updating assistant: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error updating assistant: {e}")
            raise

    def get_vector_store_files(self, vector_store_id: str) -> List[str]:
        """Get list of files in a vector store."""
        try:
            files = self.client.vector_stores.files.list(vector_store_id)
            file_names = []
            for file_obj in files.data:
                try:
                    file_details = self.client.files.retrieve(file_obj.id)
                    file_names.append(file_details.filename)
                except Exception as e:
                    self.logger.warning(f"Could not retrieve file details for {file_obj.id}: {e}")
            return file_names
        except openai.APIError as e:
            self.logger.error(f"OpenAI API error listing vector store files: {e}")
            return []

    def sync_files(self, file_paths: List[str]) -> None:
        """Synchronize local files with the vector store."""
        if not self.vector_store_id:
            self.logger.error("No vector store ID found. Cannot sync files.")
            return
        
        self.logger.info("Starting file synchronization...")
        
        # Get current files in vector store
        current_files = self.get_vector_store_files(self.vector_store_id)
        self.logger.info(f"Current files in vector store: {current_files}")
        
        # Get local files
        valid_local_files = self.validate_files(file_paths)
        local_filenames = [Path(path).name for path in valid_local_files]
        self.logger.info(f"Local files to sync: {local_filenames}")
        
        # Find files to add
        files_to_add = [path for path in valid_local_files 
                       if Path(path).name not in current_files]
        
        if files_to_add:
            self.logger.info(f"Adding {len(files_to_add)} new files to vector store")
            self.upload_files_to_vector_store(self.vector_store_id, files_to_add)
        else:
            self.logger.info("No new files to add")

    def save_env_variable(self, key: str, value: str) -> None:
        """Save a variable to the .env file."""
        try:
            env_file = '.env'
            set_key(env_file, key, value)
            self.logger.info(f"Saved {key} to {env_file}")
        except Exception as e:
            self.logger.error(f"Failed to save {key} to .env: {e}")
            raise


def main():
    """Main entry point for the assistant management script."""
    parser = argparse.ArgumentParser(
        description="Manage OpenAI assistants for ACIMguide project",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python manage_assistant.py create                    # Create new assistant
  python manage_assistant.py create --force           # Force recreate assistant
  python manage_assistant.py update --model gpt-4o    # Update assistant model
  python manage_assistant.py sync-files               # Sync files to vector store
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new assistant')
    create_parser.add_argument('--force', action='store_true', 
                             help='Force creation even if assistant already exists')
    create_parser.add_argument('--name', default='CourseGPT', 
                             help='Assistant name (default: CourseGPT)')
    create_parser.add_argument('--model', default='gpt-5-chat-latest', 
                             help='Model to use (default: gpt-5-chat-latest)')
    create_parser.add_argument('--files', nargs='*', default=DEFAULT_FILE_PATHS,
                             help='Files to upload to vector store')
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update existing assistant')
    update_parser.add_argument('--model', help='New model to use')
    update_parser.add_argument('--name', help='New assistant name')
    update_parser.add_argument('--instructions', help='New instructions')
    
    # Sync files command
    sync_parser = subparsers.add_parser('sync-files', help='Sync files to vector store')
    sync_parser.add_argument('--files', nargs='*', default=DEFAULT_FILE_PATHS,
                           help='Files to sync to vector store')
    
    # Global options
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(args.verbose)
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        manager = AssistantManager(logger)
        
        if args.command == 'create':
            # Check if assistant already exists
            if manager.assistant_id and not args.force:
                logger.error(f"Assistant already exists (ID: {manager.assistant_id}). Use --force to recreate.")
                sys.exit(1)
            
            logger.info("Starting assistant creation process...")
            
            # Create vector store
            vector_store_id = manager.create_vector_store()
            manager.save_env_variable('VECTOR_STORE_ID', vector_store_id)
            
            # Upload files
            manager.upload_files_to_vector_store(vector_store_id, args.files)
            
            # Create assistant
            assistant_id = manager.create_assistant(
                name=args.name, 
                model=args.model, 
                vector_store_id=vector_store_id
            )
            manager.save_env_variable('ASSISTANT_ID', assistant_id)
            
            logger.info("Assistant creation completed successfully!")
            
        elif args.command == 'update':
            if not manager.assistant_id:
                logger.error("No assistant ID found. Please create an assistant first.")
                sys.exit(1)
            
            # Build update parameters
            update_params = {}
            if args.model:
                update_params['model'] = args.model
            if args.name:
                update_params['name'] = args.name
            if args.instructions:
                update_params['instructions'] = args.instructions
            
            if not update_params:
                logger.error("No update parameters specified")
                sys.exit(1)
            
            manager.update_assistant(manager.assistant_id, **update_params)
            logger.info("Assistant update completed successfully!")
            
        elif args.command == 'sync-files':
            if not manager.vector_store_id:
                logger.error("No vector store ID found. Please create an assistant first.")
                sys.exit(1)
            
            manager.sync_files(args.files)
            logger.info("File synchronization completed successfully!")
        
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        if args.verbose:
            logger.exception("Full error details:")
        sys.exit(1)


if __name__ == "__main__":
    main()
