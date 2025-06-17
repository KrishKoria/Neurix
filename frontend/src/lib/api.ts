import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Types
export interface User {
  id: number;
  name: string;
  email: string;
}

export interface Group {
  id: number;
  name: string;
  users: User[];
  total_expenses: number;
}

export interface ExpenseSplitInput {
  user_id: number;
  percentage?: number;
}

export interface ExpenseCreate {
  description: string;
  amount: number;
  paid_by: number;
  split_type: "equal" | "percentage";
  splits?: ExpenseSplitInput[];
}

export interface Balance {
  user_id: number;
  user_name: string;
  balance: number;
}

export interface UserBalance {
  group_id: number;
  group_name: string;
  balance: number;
}

// API functions
export const apiService = {
  // Users
  async createUser(name: string, email: string): Promise<User> {
    const response = await api.post("/users", { name, email });
    return response.data;
  },

  async getUsers(): Promise<User[]> {
    const response = await api.get("/users");
    return response.data;
  },

  // Groups
  async createGroup(name: string, user_ids: number[]): Promise<Group> {
    const response = await api.post("/groups", { name, user_ids });
    return response.data;
  },

  async getGroup(groupId: number): Promise<Group> {
    const response = await api.get(`/groups/${groupId}`);
    return response.data;
  },

  // Expenses
  async createExpense(
    groupId: number,
    expense: ExpenseCreate
  ): Promise<{ message: string; expense_id: number }> {
    const response = await api.post(`/groups/${groupId}/expenses`, expense);
    return response.data;
  },

  // Balances
  async getGroupBalances(groupId: number): Promise<Balance[]> {
    const response = await api.get(`/groups/${groupId}/balances`);
    return response.data;
  },

  async getUserBalances(userId: number): Promise<UserBalance[]> {
    const response = await api.get(`/users/${userId}/balances`);
    return response.data;
  },

  // Health check
  async healthCheck(): Promise<{ status: string; database: string }> {
    const response = await api.get("/health");
    return response.data;
  },
};
