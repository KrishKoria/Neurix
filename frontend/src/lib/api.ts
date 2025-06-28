import axios from "axios";

const getApiUrl = () => {
  const baseUrl =
    typeof window !== "undefined"
      ? import.meta.env.VITE_API_URL || "http://localhost:8000"
      : import.meta.env.VITE_API_URL || "http://backend:8000";

  // Add API versioning prefix
  return `${baseUrl}/api/v1`;
};

const API_BASE_URL = getApiUrl();

console.log("API Base URL:", API_BASE_URL); // For debugging

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use(
  (config) => {
    console.log("Making request to:", config.baseURL! + config.url);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error("API Error:", error.message);
    if (error.response) {
      console.error("Response status:", error.response.status);
      console.error("Response data:", error.response.data);
    }
    return Promise.reject(error);
  }
);

// Types
export interface User {
  id: number;
  name: string;
  email: string;
  created_at: string; // ISO 8601 datetime string
}

export interface Group {
  id: number;
  name: string;
  users: User[];
  total_expenses: number;
  created_at: string; // ISO 8601 datetime string
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

export interface ExpenseSplit {
  user_id: number;
  user_name: string;
  amount: number;
  percentage?: number;
}

export interface Expense {
  id: number;
  description: string;
  amount: number;
  group_id: number;
  paid_by: number;
  paid_by_name: string;
  split_type: string;
  splits: ExpenseSplit[];
  created_at: string;
}

export interface Balance {
  user_id: number;
  user_name: string;
  balance: number;
  paid_total: number;
  owes_total: number;
}

export interface UserBalance {
  group_id: number;
  group_name: string;
  balance: number;
}

export interface ChatbotQuery {
  query: string;
  user_context?: any;
}

export interface ChatbotResponse {
  response: string;
  context_used?: any;
}

export interface ChatMessage {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
}

// API functions
export const apiService = {
  // Users
  async createUser(name: string, email: string): Promise<User> {
    const response = await api.post("/users/", { name, email });
    return response.data;
  },

  async getUsers(): Promise<User[]> {
    const response = await api.get("/users/");
    return response.data;
  },

  async getUser(userId: number): Promise<User> {
    const response = await api.get(`/users/${userId}/`);
    return response.data;
  },

  async updateUser(userId: number, name: string, email: string): Promise<User> {
    const response = await api.put(`/users/${userId}/`, { name, email });
    return response.data;
  },

  async deleteUser(userId: number): Promise<{ message: string }> {
    const response = await api.delete(`/users/${userId}/`);
    return response.data;
  },

  async getUserSummary(userId: number): Promise<any> {
    const response = await api.get(`/users/${userId}/summary`);
    return response.data;
  },

  // Groups
  async createGroup(name: string, user_ids: number[]): Promise<Group> {
    const response = await api.post("/groups/", { name, user_ids });
    return response.data;
  },

  async getGroup(groupId: number): Promise<Group> {
    const response = await api.get(`/groups/${groupId}/`);
    return response.data;
  },
  async getAllGroups(): Promise<Group[]> {
    try {
      const response = await api.get("/groups/");
      return response.data;
    } catch (error) {
      console.warn("Get all groups endpoint not available yet");
      return [];
    }
  },

  async updateGroup(groupId: number, name: string, user_ids: number[]): Promise<Group> {
    const response = await api.put(`/groups/${groupId}/`, { name, user_ids });
    return response.data;
  },

  async deleteGroup(groupId: number): Promise<{ message: string }> {
    const response = await api.delete(`/groups/${groupId}/`);
    return response.data;
  },

  async getGroupSettlements(groupId: number): Promise<any> {
    const response = await api.get(`/groups/${groupId}/settlements`);
    return response.data;
  },

  // Expenses
  async createExpense(
    groupId: number,
    expense: ExpenseCreate
  ): Promise<Expense> {
    const response = await api.post(`/groups/${groupId}/expenses`, expense);
    return response.data;
  },

  async getExpense(expenseId: number): Promise<Expense> {
    const response = await api.get(`/expenses/${expenseId}/`);
    return response.data;
  },

  async getGroupExpenses(groupId: number): Promise<Expense[]> {
    const response = await api.get(`/groups/${groupId}/expenses`);
    return response.data;
  },

  async updateExpense(expenseId: number, expense: Partial<ExpenseCreate>): Promise<Expense> {
    const response = await api.put(`/expenses/${expenseId}/`, expense);
    return response.data;
  },

  async deleteExpense(expenseId: number): Promise<{ message: string }> {
    const response = await api.delete(`/expenses/${expenseId}/`);
    return response.data;
  },

  async getExpenseStatistics(): Promise<any> {
    const response = await api.get("/expenses/statistics");
    return response.data;
  },

  async queryChatbot(query: string): Promise<ChatbotResponse> {
    const response = await api.post("/chatbot/", { query });
    return response.data;
  },
  // Health check
  async healthCheck(): Promise<{ status: string; database: string }> {
    // Health endpoint doesn't use API versioning
    const baseUrl =
      typeof window !== "undefined"
        ? import.meta.env.VITE_API_URL || "http://localhost:8000"
        : import.meta.env.VITE_API_URL || "http://backend:8000";

    const response = await axios.get(`${baseUrl}/health`);
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
};
