#!/usr/bin/env python3
"""
BigCommerce Coupon Code Uploader CLI
Upload promotional coupon codes from a text file to BigCommerce store.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any
import requests
import csv

RED   = "\033[31m"
RESET = "\033[0m"


class BigCommerceAPI:
    """BigCommerce API client for coupon operations."""
    
    def __init__(self, store_hash: str, access_token: str):
        self.store_hash = store_hash
        self.access_token = access_token
        self.base_url = f"https://api.bigcommerce.com/stores/{store_hash}/v3"
        self.headers = {
            "X-Auth-Token": access_token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def get_promotions(self) -> List[Dict[str, Any]]:
        """Get all promotions from the store."""
        url = f"{self.base_url}/promotions?limit=250"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json().get("data", [])
    
    def get_promotion_by_id(self, promotion_id: int) -> Dict[str, Any]:
        """Get a specific promotion by ID."""
        url = f"{self.base_url}/promotions/{promotion_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json().get("data", {})

    def create_coupon_codes(self, promotion_id: int, codes: List[Dict[str, Any]]):
        success = []
        errors = []

        for row in codes: 
            try:
                self.create_coupon_code(promotion_id, row)
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 422:
                    errors.append({"message" : "Duplicate code.", "code": row['code']})
                elif e.response.status_code == 400:
                    errors.append({"message" : "Error importing code.", "code": row['code']})
                elif e.response.status_code == 401:
                    errors.append({"message" : "Error importing code.", "code": row['code']})
            except Exception as e:
                errors.append({"message" : "Error importing code.", "code": row['code']})
            else:
                success.append({"code": row['code']})
        
        return (success, errors)
    
    def create_coupon_code(self, promotion_id: int, code_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create coupon codes for a specific promotion."""
        url = f"{self.base_url}/promotions/{promotion_id}/codes"
        
        # Format codes for API
        coupon_data = {
            "code": code_data["code"],
            "max_uses": code_data["max_uses"],
            "max_uses_per_customer": code_data["max_uses_per_customer"]
        }
        
        response = requests.post(url, headers=self.headers, json=coupon_data)
        response.raise_for_status()
        return response.json()


def read_coupon_codes(file_path: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Read coupon codes from a CSV file with Code, MaxUses, MaxUsesPerCustomer columns."""
    try:
        codes = []
        with open(file_path, 'r', encoding='utf-8') as file:
            # Check if file is empty
            first_char = file.read(1)
            if not first_char:
                print("Error: CSV file is empty.")
                sys.exit(1)
            file.seek(0)  # Reset file pointer
            
            csv_reader = csv.DictReader(file)
            
            # Validate required columns
            required_columns = {'Code', 'MaxUses', 'MaxUsesPerCustomer'}
            if not required_columns.issubset(csv_reader.fieldnames or []):
                print(f"Error: CSV file must contain columns: {', '.join(required_columns)}")
                print(f"Found columns: {', '.join(csv_reader.fieldnames or [])}")
                sys.exit(1)
            
            row_number = 1  # Start at 1 since we have headers
            for row in csv_reader:
                row_number += 1
                
                # Skip empty rows
                if not any(row.values()):
                    continue
                
                code = row['Code'].strip()
                if not code:
                    print(f"Warning: Empty code found at row {row_number}, skipping.")
                    continue
                
                try:
                    max_uses = 0 # Default is 0 which means unlimited
                    max_uses_per_customer = 0 # Default is 0 which means unlimited
                    
                    if row['MaxUses'].strip():
                        max_uses = int(row['MaxUses'].strip())
                        if max_uses < 0:
                            print(f"Warning: Invalid MaxUses value at row {row_number} (must be >= 0), skipping.")
                            continue
                    
                    if row['MaxUsesPerCustomer'].strip():
                        max_uses_per_customer = int(row['MaxUsesPerCustomer'].strip())
                        if max_uses_per_customer < 0:
                            print(f"Warning: Invalid MaxUsesPerCustomer value at row {row_number} (must be >= 0), skipping.")
                            continue
                    
                    codes.append({
                        'code': code,
                        'max_uses': max_uses,
                        'max_uses_per_customer': max_uses_per_customer
                    })
                
                except ValueError as e:
                    print(f"Warning: Invalid number format at row {row_number}, skipping. Error: {e}")
                    continue
        
        if not codes:
            print("No valid coupon codes found in CSV file.")
            sys.exit(1)
        
        if len(codes) > limit:
            print(f"Warning: File contains {len(codes)} codes. Only first {limit} will be uploaded.")
            codes = codes[:limit]
        
        return codes
    
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
    except csv.Error as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

def validate_promotion(api: BigCommerceAPI, promotion_id: int) -> bool:
    """Validate that the promotion exists and is suitable for coupon codes."""
    try:
        promotion = api.get_promotion_by_id(promotion_id)
        
        if not promotion:
            print(f"Error: Promotion with ID {promotion_id} not found.")
            return False
        
        # Check if promotion supports coupon codes
        if promotion.get("redemption_type") != "COUPON":
            print(f"Error: Promotion '{promotion.get('name')}' does not support coupon codes.")
            return False
        
        print(f"Found promotion: '{promotion.get('name')}' (ID: {promotion_id})")
        return True
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"Error: Promotion with ID {promotion_id} not found.")
        else:
            print(f"Error validating promotion: {e}")
        return False
    except Exception as e:
        print(f"Error validating promotion: {e}")
        return False


def list_promotions(api: BigCommerceAPI):
    """List all available promotions."""
    try:
        promotions = api.get_promotions()
        
        if not promotions:
            print("No promotions found in your store.")
            return
        
        print("\nAvailable Promotions:")
        print("-" * 80)
        print(f"{'ID':<8} {'Name':<30} {'Type':<15}")
        print("-" * 80)
        
        for promo in promotions:
            print(f"{promo.get('id', 'N/A'):<8} "
                  f"{promo.get('name', 'N/A')[:29]:<30} "
                  f"{promo.get('redemption_type', 'N/A'):<15}")
        
        print("-" * 80)

    except Exception as e:
        print(f"Error listing promotions: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Upload coupon codes to BigCommerce promotional campaigns",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --store-hash abc123 --token your_token --promotion-id 1 --file codes.txt
  %(prog)s --store-hash abc123 --token your_token --list-promotions
  
File format:
  The CSV file should contain 3 columns: Code,MaxUses,MaxUsesPerCustomer like this:
  Code,MaxUses,MaxUsesPerCustomer
  SAVE10,1,1
  WELCOME20,1,1
  FREESHIP,1,1
        """
    )
    
    parser.add_argument(
        "--store-hash",
        required=True,
        help="BigCommerce store hash"
    )
    
    parser.add_argument(
        "--token",
        required=True,
        help="BigCommerce API access token"
    )
    
    parser.add_argument(
        "--promotion-id",
        type=int,
        help="ID of the promotion to add coupon codes to"
    )
    
    parser.add_argument(
        "--file",
        help="Path to text file containing coupon codes (one per line)"
    )
    
    parser.add_argument(
        "--list-promotions",
        action="store_true",
        help="List all available promotions"
    )
    
    parser.add_argument(
        "--max-codes",
        type=int,
        default=100,
        help="Maximum number of codes to upload (default: 100)"
    )
    
    args = parser.parse_args()
    
    # Initialize API client
    api = BigCommerceAPI(args.store_hash, args.token)
    
    # List promotions if requested
    if args.list_promotions:
        list_promotions(api)
        return
    
    # Validate required arguments for upload
    if not args.promotion_id or not args.file:
        print("Error: --promotion-id and --file are required for uploading codes.")
        print("Use --list-promotions to see available promotions.")
        sys.exit(1)
    
    # Validate file exists
    if not Path(args.file).exists():
        print(f"Error: File '{args.file}' not found.")
        sys.exit(1)
    
    # Validate promotion
    if not validate_promotion(api, args.promotion_id):
        sys.exit(1)
    
    # Read coupon codes
    print(f"Reading coupon codes from '{args.file}'...")
    codes = read_coupon_codes(args.file, args.max_codes)
    
    if not codes:
        print("No valid coupon codes found in file.")
        sys.exit(1)
    
    print(f"Found {len(codes)} coupon codes to upload.")
    
    # Confirm upload
    response = input(f"Upload {len(codes)} codes to promotion {args.promotion_id}? (y/N): ")
    if response.lower() != 'y':
        print("Upload cancelled.")
        sys.exit(0)
    
    # Upload codes
    try:
        print("Uploading coupon codes...")
        (created_codes, errors) = api.create_coupon_codes(args.promotion_id, codes)
         
        print(f"\nUpload complete!")
        print(f"Successfully created: {len(created_codes)} codes")
        
        if errors:
            print("-" * 80)
            print(f"{'Code':<32} {'Message':<128}")
            print("-" * 80)
            for error in errors[:5]:  # Show first 5 errors
                print(RED
                      + f"{error.get('code'):<32} "
                      + f"{error.get('message')[:128]:<128}"
                      + RESET
                )
            if len(errors) > 5:
                print(f"  ... and {len(errors) - 5} more errors")
    except Exception as e:
        print(f"Error uploading codes: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
