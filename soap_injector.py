#!/usr/bin/env python3
"""
SOAP Injector with automatic variable substitution
Sends random SOAP messages with UUID generation and custom variables
"""

import os
import re
import uuid
import random
import logging
import requests
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import time

class SOAPInjector:
    def __init__(self, soap_dir: str, endpoint: str, timeout: int = 30):
        """
        Initialize the SOAP injector
        
        Args:
            soap_dir: Directory containing SOAP files
            endpoint: SOAP endpoint URL
            timeout: HTTP request timeout
        """
        self.soap_dir = Path(soap_dir)
        self.endpoint = endpoint
        self.timeout = timeout
        self.soap_files = []
        self.session = requests.Session()
        
        # Configure logging
        self._setup_logging()
        
        # Load SOAP files
        self._load_soap_files()
    
    def _setup_logging(self):
        """Configure the logging system"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        self.logger = logging.getLogger(__name__)
    
    def _load_soap_files(self):
        """Load the list of available SOAP files"""
        if not self.soap_dir.exists():
            raise FileNotFoundError(f"📁 SOAP directory not found: {self.soap_dir}")
        
        # Search for all XML files in the directory
        self.soap_files = list(self.soap_dir.glob("*.xml"))
        
        if not self.soap_files:
            raise ValueError(f"📄 No XML files found in: {self.soap_dir}")
        
        self.logger.info(f"📚 Loaded {len(self.soap_files)} SOAP file(s) from {self.soap_dir}")
        for file in self.soap_files:
            self.logger.info(f"   📄 {file.name}")
    
    def _generate_variables(self) -> Dict[str, str]:
        """
        Generate replacement variables
        
        Returns:
            Dictionary of variables with their values
        """
        now = datetime.now()
        
        variables = {
            # UUID
            'UUID': str(uuid.uuid4()),
            'UUID_UPPER': str(uuid.uuid4()).upper(),
            'UUID_NO_DASH': str(uuid.uuid4()).replace('-', ''),
            
            # Timestamps
            'TIMESTAMP': now.strftime('%Y-%m-%dT%H:%M:%S'),
            'TIMESTAMP_MS': now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3],
            'DATE': now.strftime('%Y-%m-%d'),
            'TIME': now.strftime('%H:%M:%S'),
            'EPOCH': str(int(now.timestamp())),
            
            # Random identifiers
            'RANDOM_ID': str(random.randint(100000, 999999)),
            'RANDOM_ALPHA': ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=8)),
            'RANDOM_ALPHANUM': ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=10)),
        }
        
        return variables
    
    def _replace_variables(self, content: str, variables: Dict[str, str]) -> str:
        """
        Replace variables in SOAP content
        
        Supported format: {{VARIABLE_NAME}}
        
        Args:
            content: Original SOAP content
            variables: Variables to replace
            
        Returns:
            Content with replaced variables
        """
        result = content
        
        for var_name, var_value in variables.items():
            pattern = f"{{{{{var_name}}}}}"
            result = result.replace(pattern, var_value)
        
        return result
    
    def _select_random_soap(self) -> Path:
        """Select a random SOAP file"""
        return random.choice(self.soap_files)
    
    def _load_soap_content(self, soap_file: Path) -> str:
        """Load the content of a SOAP file"""
        try:
            with open(soap_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            self.logger.error(f"❌ Error reading {soap_file.name}: {e}")
            raise
    
    def _send_soap_request(self, content: str, soap_file: str) -> bool:
        """
        Send a SOAP request
        
        Args:
            content: SOAP content to send
            soap_file: SOAP file name for logging
            
        Returns:
            True if success (HTTP 200), False otherwise
        """
        headers = {
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': '""',  # Empty SOAPAction by default
        }
        
        try:
            response = self.session.post(
                self.endpoint,
                data=content.encode('utf-8'),
                headers=headers,
                timeout=self.timeout
            )
            
            # HTTP status verification
            if response.status_code == 200:
                self.logger.info(f"✅ [{soap_file}] → {self.endpoint} | HTTP {response.status_code} | {len(response.content)} bytes")
                return True
            else:
                self.logger.warning(f"⚠️ [{soap_file}] → {self.endpoint} | HTTP {response.status_code} | {response.reason}")
                self.logger.debug(f"Response: {response.text[:200]}...")
                return False
                
        except requests.exceptions.Timeout:
            self.logger.error(f"⏰ [{soap_file}] → {self.endpoint} | Timeout after {self.timeout}s")
            return False
        except requests.exceptions.ConnectionError:
            self.logger.error(f"🔌 [{soap_file}] → {self.endpoint} | Connection failed - endpoint unreachable")
            return False
        except Exception as e:
            self.logger.error(f"💥 [{soap_file}] → {self.endpoint} | Unexpected error: {type(e).__name__}: {e}")
            return False
    
    def inject_single(self) -> bool:
        """
        Inject a single SOAP message
        
        Returns:
            True if success, False otherwise
        """
        # Random selection of a SOAP file
        soap_file = self._select_random_soap()
        
        # Load content
        content = self._load_soap_content(soap_file)
        
        # Generate variables
        variables = self._generate_variables()
        
        # Replace variables
        processed_content = self._replace_variables(content, variables)
        
        # Log generated variables (debug)
        self.logger.debug(f"Generated variables: {list(variables.keys())}")
        
        # Send request
        return self._send_soap_request(processed_content, soap_file.name)
    
    def inject_multiple(self, count: int, delay: float = 0.0) -> Dict[str, int]:
        """
        Inject multiple SOAP messages
        
        Args:
            count: Number of messages to send
            delay: Delay between each send (seconds)
            
        Returns:
            Send statistics
        """
        stats = {'success': 0, 'failed': 0, 'total': count}
        
        self.logger.info(f"🚀 Starting injection of {count} SOAP message(s)")
        start_time = time.time()
        
        for i in range(1, count + 1):
            success = self.inject_single()
            
            if success:
                stats['success'] += 1
            else:
                stats['failed'] += 1
            
            # Delay between sends
            if delay > 0 and i < count:
                self.logger.info(f"⏳ Waiting {delay}s before next send...")
                time.sleep(delay)
        
        elapsed = time.time() - start_time
        success_rate = (stats['success'] / stats['total']) * 100
        
        # Create a nice statistics box
        box_width = 50
        
        def format_box_line(text):
            """Format a line to fit perfectly in the box"""
            # Calculate actual display width accounting for emojis
            visual_length = len(text)
            # Each emoji takes 2 display positions but counts as 1 in string length
            emoji_count = sum(1 for char in text if ord(char) > 127)
            visual_length += emoji_count
            
            padding_needed = box_width - 3 - visual_length  # 3 for "│ " and "│"
            return f"│ {text}{' ' * padding_needed}│"
        
        self.logger.info("┌" + "─" * (box_width - 2) + "┐")
        self.logger.info(format_box_line("📊 INJECTION SUMMARY"))
        self.logger.info("├" + "─" * (box_width - 2) + "┤")
        self.logger.info(format_box_line(f"🏁 Completed in: {elapsed:.2f}s"))
        self.logger.info(format_box_line(f"✅ Success: {stats['success']}/{stats['total']} ({success_rate:.1f}%)"))
        self.logger.info(format_box_line(f"❌ Failed: {stats['failed']}/{stats['total']}"))
        self.logger.info("└" + "─" * (box_width - 2) + "┘")
        
        return stats


def main():
    parser = argparse.ArgumentParser(description='SOAP Injector with variable substitution')
    parser.add_argument('endpoint', help='SOAP endpoint URL')
    parser.add_argument('--soap-dir', '-d', default='./soap_templates', 
                       help='Directory containing SOAP files (default: ./soap_templates)')
    parser.add_argument('--count', '-c', type=int, default=1,
                       help='Number of messages to send (default: 1)')
    parser.add_argument('--delay', '-w', type=float, default=0.0,
                       help='Delay between sends in seconds (default: 0)')
    parser.add_argument('--timeout', '-t', type=int, default=30,
                       help='HTTP request timeout (default: 30s)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose mode (debug)')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        injector = SOAPInjector(args.soap_dir, args.endpoint, args.timeout)
        
        if args.count == 1:
            success = injector.inject_single()
            exit(0 if success else 1)
        else:
            stats = injector.inject_multiple(args.count, args.delay)
            exit(0 if stats['failed'] == 0 else 1)
            
    except Exception as e:
        logging.error(f"💀 Fatal error: {e}")
        exit(1)


if __name__ == "__main__":
    main()