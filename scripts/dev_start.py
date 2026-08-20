#!/usr/bin/env python3
"""
AssetPilot AI Local Development Helper Script
"""
import subprocess
import sys
import os

def main():
    print("=" * 60)
    print("       AssetPilot AI - Phase 0 Development Shell       ")
    print("=" * 60)
    
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    backend_dir = os.path.join(root_dir, "backend")
    frontend_dir = os.path.join(root_dir, "frontend")
    
    print(f"[+] Root Workspace: {root_dir}")
    print(f"[+] Backend Directory: {backend_dir}")
    print(f"[+] Frontend Directory: {frontend_dir}")
    print("-" * 60)
    print("To launch services individually:")
    print("  Backend : cd backend && python -m app.main")
    print("  Frontend: cd frontend && npm run dev")
    print("=" * 60)

if __name__ == "__main__":
    main()
