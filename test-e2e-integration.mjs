#!/usr/bin/env node

/**
 * Comprehensive End-to-End API Integration Test
 * Tests the complete user workflow: create users, groups, expenses, and check balances
 */

import axios from "axios";

const API_BASE_URL = "http://localhost:8000/api/v1";

const testConfig = {
  timeout: 10000,
  headers: {
    "Content-Type": "application/json",
  },
};

class E2ETestSuite {
  constructor() {
    this.passed = 0;
    this.failed = 0;
    this.results = [];
    this.testData = {};
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
      console.log(
        `   Details: ${
          error.response?.data
            ? JSON.stringify(error.response.data)
            : error.stack
        }`
      );
    }
  }

  async runE2ETests() {
    console.log("🚀 Starting End-to-End Integration Tests\n");

    // Test 1: Create Test Users
    await this.test("Create Test User 1", async () => {
      const response = await axios.post(
        `${API_BASE_URL}/users/`,
        {
          name: "Alice Test",
          email: `alice.test.${Date.now()}@example.com`,
        },
        testConfig
      );

      if (response.status !== 200)
        throw new Error(`Expected 200, got ${response.status}`);
      if (!response.data.id) throw new Error("Missing user ID");

      this.testData.user1 = response.data;
      console.log(
        `   Created user: ${response.data.name} (ID: ${response.data.id})`
      );
    });

    await this.test("Create Test User 2", async () => {
      const response = await axios.post(
        `${API_BASE_URL}/users/`,
        {
          name: "Bob Test",
          email: `bob.test.${Date.now()}@example.com`,
        },
        testConfig
      );

      if (response.status !== 200)
        throw new Error(`Expected 200, got ${response.status}`);
      if (!response.data.id) throw new Error("Missing user ID");

      this.testData.user2 = response.data;
      console.log(
        `   Created user: ${response.data.name} (ID: ${response.data.id})`
      );
    });

    // Test 2: Create Test Group
    await this.test("Create Test Group", async () => {
      if (!this.testData.user1 || !this.testData.user2) {
        throw new Error("Users not created, skipping group creation");
      }

      const response = await axios.post(
        `${API_BASE_URL}/groups/`,
        {
          name: `Test Group ${Date.now()}`,
          user_ids: [this.testData.user1.id, this.testData.user2.id],
        },
        testConfig
      );

      if (response.status !== 200)
        throw new Error(`Expected 200, got ${response.status}`);
      if (!response.data.id) throw new Error("Missing group ID");
      if (response.data.users.length !== 2)
        throw new Error("Group should have 2 users");

      this.testData.group = response.data;
      console.log(
        `   Created group: ${response.data.name} (ID: ${response.data.id})`
      );
    });

    // Test 3: Create Expense
    await this.test("Create Equal Split Expense", async () => {
      if (!this.testData.group) {
        throw new Error("Group not created, skipping expense creation");
      }

      const response = await axios.post(
        `${API_BASE_URL}/groups/${this.testData.group.id}/expenses`,
        {
          description: "Test Restaurant Bill",
          amount: 120.0,
          paid_by: this.testData.user1.id,
          split_type: "equal",
        },
        testConfig
      );

      if (response.status !== 200)
        throw new Error(`Expected 200, got ${response.status}`);
      if (!response.data.id) throw new Error("Missing expense ID");
      if (response.data.splits.length !== 2)
        throw new Error("Should have 2 splits");
      if (response.data.splits[0].amount !== 60)
        throw new Error("Equal split should be 60 each");

      this.testData.expense1 = response.data;
      console.log(
        `   Created expense: ${response.data.description} ($${response.data.amount})`
      );
    });

    // Test 4: Create Percentage Split Expense
    await this.test("Create Percentage Split Expense", async () => {
      if (!this.testData.group) {
        throw new Error("Group not created, skipping expense creation");
      }

      const response = await axios.post(
        `${API_BASE_URL}/groups/${this.testData.group.id}/expenses`,
        {
          description: "Test Grocery Bill",
          amount: 80.0,
          paid_by: this.testData.user2.id,
          split_type: "percentage",
          splits: [
            { user_id: this.testData.user1.id, percentage: 30 },
            { user_id: this.testData.user2.id, percentage: 70 },
          ],
        },
        testConfig
      );

      if (response.status !== 200)
        throw new Error(`Expected 200, got ${response.status}`);
      if (!response.data.id) throw new Error("Missing expense ID");
      if (response.data.splits.length !== 2)
        throw new Error("Should have 2 splits");

      this.testData.expense2 = response.data;
      console.log(
        `   Created expense: ${response.data.description} ($${response.data.amount})`
      );
    });

    // Test 5: Check Group Balances
    await this.test("Check Group Balances", async () => {
      if (!this.testData.group) {
        throw new Error("Group not created, skipping balance check");
      }

      const response = await axios.get(
        `${API_BASE_URL}/groups/${this.testData.group.id}/balances`,
        testConfig
      );

      if (response.status !== 200)
        throw new Error(`Expected 200, got ${response.status}`);
      if (!Array.isArray(response.data))
        throw new Error("Balances should be an array");
      if (response.data.length !== 2)
        throw new Error("Should have 2 balance entries");

      // Check balance calculations
      const user1Balance = response.data.find(
        (b) => b.user_id === this.testData.user1.id
      );
      const user2Balance = response.data.find(
        (b) => b.user_id === this.testData.user2.id
      );

      if (!user1Balance || !user2Balance)
        throw new Error("Missing balance data");

      // User1 paid $120, owes $60 (equal) + $24 (30% of $80) = $84
      // Net: $120 - $84 = +$36
      const expectedUser1Balance = 120 - (60 + 24); // Should be +36

      // User2 paid $80, owes $60 (equal) + $56 (70% of $80) = $116
      // Net: $80 - $116 = -$36
      const expectedUser2Balance = 80 - (60 + 56); // Should be -36

      if (Math.abs(user1Balance.balance - expectedUser1Balance) > 0.01) {
        throw new Error(
          `User1 balance wrong: expected ${expectedUser1Balance}, got ${user1Balance.balance}`
        );
      }

      if (Math.abs(user2Balance.balance - expectedUser2Balance) > 0.01) {
        throw new Error(
          `User2 balance wrong: expected ${expectedUser2Balance}, got ${user2Balance.balance}`
        );
      }

      console.log(`   User1 balance: $${user1Balance.balance}`);
      console.log(`   User2 balance: $${user2Balance.balance}`);
    });

    // Test 6: Check User Balances
    await this.test("Check User Balances Across Groups", async () => {
      if (!this.testData.user1) {
        throw new Error("User not created, skipping user balance check");
      }

      const response = await axios.get(
        `${API_BASE_URL}/users/${this.testData.user1.id}/balances`,
        testConfig
      );

      if (response.status !== 200)
        throw new Error(`Expected 200, got ${response.status}`);
      if (!Array.isArray(response.data))
        throw new Error("User balances should be an array");

      console.log(`   User has balances in ${response.data.length} groups`);
    });

    // Test 7: Test Chatbot with Real Data
    await this.test("Test Chatbot with Group Data", async () => {
      if (!this.testData.group) {
        throw new Error("Group not created, skipping chatbot test");
      }

      const response = await axios.post(
        `${API_BASE_URL}/chatbot/`,
        {
          query: `What are the balances in group ${this.testData.group.id}?`,
        },
        testConfig
      );

      if (response.status !== 200)
        throw new Error(`Expected 200, got ${response.status}`);
      if (!response.data.response) throw new Error("Missing chatbot response");

      console.log(
        `   Chatbot response: ${response.data.response.substring(0, 100)}...`
      );
    });

    this.printResults();
  }

  printResults() {
    console.log("\n📊 End-to-End Test Results:");
    console.log("===============================");

    this.results.forEach((result) => {
      const icon = result.status === "PASSED" ? "✅" : "❌";
      console.log(`${icon} ${result.name}: ${result.status}`);
    });

    console.log(`\n📈 Summary: ${this.passed} passed, ${this.failed} failed`);

    if (this.failed === 0) {
      console.log(
        "🎉 All E2E tests passed! The application is working end-to-end."
      );
      console.log(
        "🌐 Frontend should be able to use all API functionality successfully."
      );
    } else {
      console.log(
        "⚠️  Some E2E tests failed. Check the backend implementation."
      );
    }

    // Print test data summary
    console.log("\n📋 Test Data Created:");
    if (this.testData.user1)
      console.log(
        `   User 1: ${this.testData.user1.name} (${this.testData.user1.email})`
      );
    if (this.testData.user2)
      console.log(
        `   User 2: ${this.testData.user2.name} (${this.testData.user2.email})`
      );
    if (this.testData.group)
      console.log(
        `   Group: ${this.testData.group.name} (${this.testData.group.users.length} users)`
      );
    if (this.testData.expense1)
      console.log(
        `   Expense 1: ${this.testData.expense1.description} ($${this.testData.expense1.amount})`
      );
    if (this.testData.expense2)
      console.log(
        `   Expense 2: ${this.testData.expense2.description} ($${this.testData.expense2.amount})`
      );

    process.exit(this.failed > 0 ? 1 : 0);
  }
}

// Run tests if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const tester = new E2ETestSuite();
  tester.runE2ETests().catch((error) => {
    console.error("❌ E2E test runner failed:", error.message);
    process.exit(1);
  });
}

export default E2ETestSuite;
