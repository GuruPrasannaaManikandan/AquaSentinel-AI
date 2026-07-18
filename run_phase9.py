import os
import sys
import unittest
import json

# Ensure project root is on path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

def clean_stale_test_databases():
    """Removes any stale test database files from models/fusion/ to keep release clean."""
    test_db_files = [
        "test_events.db",
        "test_phase8_events.db",
        "test_phase9_events.db"
    ]
    db_dir = os.path.join(project_dir, "models", "fusion")
    for f in test_db_files:
        path = os.path.join(db_dir, f)
        if os.path.exists(path):
            try:
                os.remove(path)
                print(f"Removed stale test database: {f}")
            except Exception as e:
                print(f"Could not remove stale test database {f}: {e}")

def main():
    print("==============================================================")
    print("🚀 RUNNING FINAL PHASE 9 FORENSIC VERIFICATION & FREEZE 🚀")
    print("==============================================================")

    # 1. Preliminary File Integrity Verifications
    print("[Task 1] Checking critical releases and audit files...")
    critical_files = [
        os.path.join(project_dir, "config", "release_manifest.json"),
        os.path.join(project_dir, "config", "final_demo_scenarios.json"),
        os.path.join(project_dir, "reports", "phase9", "final_verified_metrics.json"),
        os.path.join(project_dir, "reports", "phase9", "final_metric_lineage_audit.md"),
        os.path.join(project_dir, "reports", "phase9", "scientific_claims_audit.md"),
        os.path.join(project_dir, "reports", "phase9", "project_inventory.md"),
        os.path.join(project_dir, "reports", "phase9", "active_artifact_verification.md"),
        os.path.join(project_dir, "reports", "phase9", "final_data_leakage_audit.md"),
        os.path.join(project_dir, "reports", "phase9", "final_end_to_end_verification.md"),
        os.path.join(project_dir, "reports", "phase9", "final_demo_results.md"),
        os.path.join(project_dir, "reports", "phase9", "final_performance_benchmark.md"),
        os.path.join(project_dir, "reports", "phase9", "final_resilience_verification.md"),
        os.path.join(project_dir, "reports", "phase9", "security_review.md"),
        os.path.join(project_dir, "reports", "phase9", "repository_cleanup_plan.md"),
        os.path.join(project_dir, "docs", "system_architecture.md"),
        os.path.join(project_dir, "docs", "final_technical_report.md"),
        os.path.join(project_dir, "docs", "demo_guide.md"),
        os.path.join(project_dir, "docs", "viva_questions_and_answers.md"),
        os.path.join(project_dir, "docs", "future_hardware_migration.md"),
        os.path.join(project_dir, "docs", "final_release_checklist.md"),
        os.path.join(project_dir, "README.md"),
    ]

    missing = []
    for f in critical_files:
        if not os.path.exists(f):
            missing.append(f)

    if missing:
        print(f"Error: {len(missing)} critical active files are missing!")
        for m in missing:
            print(f"  Missing: {m}")
        sys.exit(1)
    else:
        print("  All 21 critical release artifacts are present.")

    # 2. Run Complete Project Test Suite
    print("\n[Task 2] Discovering and executing the entire project test suite...")
    loader = unittest.TestLoader()
    suite = loader.discover(start_dir=os.path.join(project_dir, "tests"), pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=1)
    result = runner.run(suite)
    
    # Check execution status
    if not result.wasSuccessful():
        print("\nError: Project unit test suite run failed. Fix errors before freezing.")
        sys.exit(1)

    print(f"  All {result.testsRun} test cases passed successfully.")

    # 3. Safe Cleanup Actions
    print("\n[Task 3] Executing safe cleanup routines...")
    clean_stale_test_databases()

    print("\n==============================================================")
    print("🎉 PHASE 9 SYSTEM AUDIT & RELEASE FREEZE COMPLETE! 🎉")
    print("==============================================================")

if __name__ == "__main__":
    main()
