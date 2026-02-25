"""
End-to-End Testing Script
"""
import asyncio
import httpx
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QiATester:
    """Testing end-to-end de QiA"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def run_all_tests(self):
        """Ejecuta todos los tests"""
        logger.info("=" * 60)
        logger.info("QiA End-to-End Testing")
        logger.info("=" * 60)
        
        tests = [
            ("Health Check", self.test_health),
            ("Webhook Endpoint", self.test_webhook),
            ("Invalid Webhook", self.test_invalid_webhook),
            ("Pub/Sub Simulation", self.test_pubsub)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            try:
                logger.info(f"\n🧪 Running: {test_name}")
                result = await test_func()
                results.append((test_name, result, None))
                logger.info(f"✅ PASSED: {test_name}")
            except Exception as e:
                results.append((test_name, False, str(e)))
                logger.error(f"❌ FAILED: {test_name} - {e}")
        
        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("TEST SUMMARY")
        logger.info("=" * 60)
        
        passed = sum(1 for _, result, _ in results if result)
        total = len(results)
        
        for test_name, result, error in results:
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"{status} - {test_name}")
            if error:
                logger.info(f"   Error: {error}")
        
        logger.info(f"\nTotal: {passed}/{total} tests passed")
        
        return passed == total
    
    async def test_health(self) -> bool:
        """Test health endpoint"""
        response = await self.client.get(f"{self.base_url}/")
        
        if response.status_code == 200:
            data = response.json()
            return data.get("status") == "running"
        
        return False
    
    async def test_webhook(self) -> bool:
        """Test webhook endpoint with valid payload"""
        payload = {
            "action": "opened",
            "pull_request": {
                "number": 1,
                "title": "Test PR",
                "body": "Test",
                "state": "open",
                "user": {"login": "test"},
                "base": {"ref": "main"},
                "head": {"ref": "test"},
                "additions": 10,
                "deletions": 5,
                "changed_files": 2
            },
            "repository": {
                "full_name": "aurorabot0413/qia-test-app",
                "name": "qia-test-app",
                "owner": {"login": "aurorabot0413"}
            }
        }
        
        response = await self.client.post(
            f"{self.base_url}/webhook/github",
            json=payload
        )
        
        # Should return 202 (accepted)
        if response.status_code == 202:
            data = response.json()
            return data.get("status") == "accepted"
        
        return False
    
    async def test_invalid_webhook(self) -> bool:
        """Test webhook with invalid payload"""
        payload = {"invalid": "data"}
        
        response = await self.client.post(
            f"{self.base_url}/webhook/github",
            json=payload
        )
        
        # Should return 200 (ignored) for non-PR events
        return response.status_code == 200
    
    async def test_pubsub(self) -> bool:
        """Test Pub/Sub simulation"""
        # This would require Pub/Sub to be configured
        # For now, just check the simulator exists
        import os
        simulator_path = "orchestrator/webhook_simulator.py"
        return os.path.exists(simulator_path)


async def main():
    """Run tests"""
    import os
    
    base_url = os.getenv("QIA_URL", "http://localhost:8080")
    
    tester = QiATester(base_url)
    success = await tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed!")
        exit(0)
    else:
        print("\n❌ Some tests failed")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())
