#!/usr/bin/env node

/**
 * API Integration Test Script
 * Tests the new versioned API endpoints to ensure frontend compatibility
 */

import axios from "axios";

const API_BASE_URL = "http://localhost:8000";
const API_V1_URL = `${API_BASE_URL}/api/v1`;

// Test configuration
const testConfig = {
  timeout: 5000,
  headers: {
    "Content-Type": "application/json",
  },
};

class APITester {
  constructor() {
    this.passed = 0;
    this.failed = 0;
    this.results = [];
  }

  async test(name, testFn) {
    try {
      console.log(`🧪 Testing: ${name}`);
      await testFn();
      this.passed++;
      this.results.push({ name, status: "PASSED", error: null });
      console.log(`✅ PASSED: ${name}`);
    } catch (error) {
      this.failed++;
      this.results.push({ name, status: "FAILED", error: error.message });
      console.log(`❌ FAILED: ${name} - ${error.message}`);
    }
  }

  async runTests() {
    console.log("🚀 Starting API Integration Tests\n");

    // Test 1: Health Check (non-versioned)
    await this.test("Health Check Endpoint", async () => {
      const response = await axios.get(`${API_BASE_URL}/health`, testConfig);
      if (response.status !== 200)
        throw new Error(`Expected 200, got ${response.status}`);
      if (!response.data.status) throw new Error("Missing status field");
    });

    // Test 2: Get Users (versioned)
    await this.test("Get Users API v1", async () => {
      const response = await axios.get(`${API_V1_URL}/users`, testConfig);
      if (response.status !== 200)
        throw new Error(`Expected 200, got ${response.status}`);
      if (!Array.isArray(response.data))
        throw new Error("Response should be an array");
    });

    // Test 3: Get Groups (versioned)
    await this.test("Get Groups API v1", async () => {
      const response = await axios.get(`${API_V1_URL}/groups`, testConfig);
      if (response.status !== 200)
        throw new Error(`Expected 200, got ${response.status}`);
      if (!Array.isArray(response.data))
        throw new Error("Response should be an array");
    });

    // Test 4: Legacy Redirect
    await this.test("Legacy Endpoint Redirect", async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/users`, {
          ...testConfig,
          maxRedirects: 0, // Disable automatic redirects
          validateStatus: (status) => status === 308,
        });
        if (response.status !== 308)
          throw new Error(`Expected 308 redirect, got ${response.status}`);
        if (!response.data.new_endpoint)
          throw new Error("Missing new_endpoint in redirect response");
      } catch (error) {
        if (error.response && error.response.status === 308) {
          // This is expected - axios throws on 3xx status codes
          return;
        }
        throw error;
      }
    });

    // Test 5: API Documentation
    await this.test("API Documentation Available", async () => {
      const response = await axios.get(`${API_BASE_URL}/docs`, testConfig);
      if (response.status !== 200)
        throw new Error(`Expected 200, got ${response.status}`);
    });

    // Test 6: OpenAPI Schema
    await this.test("OpenAPI Schema", async () => {
      const response = await axios.get(
        `${API_BASE_URL}/openapi.json`,
        testConfig
      );
      if (response.status !== 200)
        throw new Error(`Expected 200, got ${response.status}`);
      if (!response.data.paths) throw new Error("Invalid OpenAPI schema");
    });

    // Test 7: Performance Headers
    await this.test("Performance Headers", async () => {
      const response = await axios.get(`${API_V1_URL}/users`, testConfig);
      if (!response.headers["x-process-time"])
        throw new Error("Missing X-Process-Time header");
      if (!response.headers["x-api-version"])
        throw new Error("Missing X-API-Version header");
    });

    // Test 8: Error Handling
    await this.test("Error Handling", async () => {
      try {
        await axios.get(`${API_V1_URL}/users/99999`, testConfig);
        throw new Error("Should have thrown 404 error");
      } catch (error) {
        if (error.response && error.response.status === 404) {
          if (!error.response.data.error)
            throw new Error("Missing error field in response");
          return; // Expected 404
        }
        throw error;
      }
    });

    this.printResults();
  }

  printResults() {
    console.log("\n📊 Test Results:");
    console.log("================");

    this.results.forEach((result) => {
      const icon = result.status === "PASSED" ? "✅" : "❌";
      console.log(`${icon} ${result.name}: ${result.status}`);
      if (result.error) {
        console.log(`   Error: ${result.error}`);
      }
    });

    console.log(`\n📈 Summary: ${this.passed} passed, ${this.failed} failed`);

    if (this.failed === 0) {
      console.log(
        "🎉 All tests passed! Frontend should work correctly with the backend."
      );
    } else {
      console.log(
        "⚠️  Some tests failed. Check the backend is running and properly configured."
      );
    }

    process.exit(this.failed > 0 ? 1 : 0);
  }
}

// Run tests if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const tester = new APITester();
  tester.runTests().catch((error) => {
    console.error("❌ Test runner failed:", error.message);
    process.exit(1);
  });
}

export default APITester;
