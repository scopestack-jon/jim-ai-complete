#!/usr/bin/env python3
"""
Update JIM AI configuration with new Knowledge Base IDs
Run this after creating a new Knowledge Base
"""

import os
import re

def update_config_files(kb_id, data_source_id):
    """Update all configuration files with new KB IDs"""

    files_to_update = [
        ('app.py', r'KB_ID = "[^"]*"', f'KB_ID = "{kb_id}"'),
        ('QUICK_START.md', r'\*\*Knowledge Base ID\*\*: `[^`]*`', f'**Knowledge Base ID**: `{kb_id}`'),
        ('QUICK_START.md', r'\*\*Data Source ID\*\*: `[^`]*`', f'**Data Source ID**: `{data_source_id}`'),
        ('QUICK_START.md', r'--knowledge-base-id [A-Z0-9]+', f'--knowledge-base-id {kb_id}'),
        ('QUICK_START.md', r'--data-source-id [A-Z0-9]+', f'--data-source-id {data_source_id}'),
        ('large-data-processor.py', r'self\.kb_id = "[^"]*"', f'self.kb_id = "{kb_id}"'),
        ('large-data-processor.py', r'self\.data_source_id = "[^"]*"', f'self.data_source_id = "{data_source_id}"'),
    ]

    for filename, pattern, replacement in files_to_update:
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                content = f.read()

            new_content = re.sub(pattern, replacement, content)

            with open(filename, 'w') as f:
                f.write(new_content)

            print(f"✅ Updated {filename}")
        else:
            print(f"⚠️  File not found: {filename}")

    # Update aws-resources.env if it exists
    if os.path.exists('aws-resources.env'):
        with open('aws-resources.env', 'r') as f:
            lines = f.readlines()

        with open('aws-resources.env', 'w') as f:
            for line in lines:
                if line.startswith('KNOWLEDGE_BASE_ID='):
                    f.write(f'KNOWLEDGE_BASE_ID={kb_id}\n')
                elif line.startswith('DATA_SOURCE_ID='):
                    f.write(f'DATA_SOURCE_ID={data_source_id}\n')
                else:
                    f.write(line)

        print("✅ Updated aws-resources.env")

if __name__ == "__main__":
    print("🔧 JIM AI Configuration Updater")
    print("=" * 50)
    print("After creating a new Knowledge Base in AWS Console,")
    print("enter the new IDs here to update all configuration files.")
    print()

    kb_id = input("Enter new Knowledge Base ID (e.g., HFCMSKWHFU): ").strip()
    data_source_id = input("Enter new Data Source ID (e.g., CZJWLDWEFD): ").strip()

    if not kb_id or not data_source_id:
        print("❌ Both IDs are required")
        exit(1)

    print()
    print("Updating configuration files...")
    update_config_files(kb_id, data_source_id)

    print()
    print("✅ Configuration updated successfully!")
    print("🚀 Next steps:")
    print("   1. Restart the web app: python3 app.py")
    print("   2. Upload your forensic data")
    print("   3. Start querying!"