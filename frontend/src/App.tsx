import React, { useState, useEffect } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Link,
  useLocation,
} from "react-router-dom";
import { 
  Users, 
  PlusCircle, 
  DollarSign, 
  BarChart3, 
  Home, 
  Settings, 
  ArrowRightLeft,
  Receipt,
  TrendingUp,
  UserCog,
  FolderOpen
} from "lucide-react";
import { apiService } from "./lib/api";
import Dashboard from "./components/Dashboard";
import CreateUser from "./components/CreateUser";
import CreateGroup from "./components/CreateGroup";
import AddExpense from "./components/AddExpense";
import GroupBalances from "./components/GroupBalances";
import UserBalances from "./components/UserBalances";
import ManageUsers from "./components/ManageUsers";
import ManageGroups from "./components/ManageGroups";
import ManageExpenses from "./components/ManageExpenses";
import Settlements from "./components/Settlements";
import ExpenseStatistics from "./components/ExpenseStatistics";
import Chatbot from "./components/ChatBot";

const Navigation = () => {
  const location = useLocation();

  const navItems = [
    { path: "/", icon: Home, label: "Dashboard" },
    { path: "/create-user", icon: Users, label: "Create User" },
    { path: "/create-group", icon: PlusCircle, label: "Create Group" },
    { path: "/add-expense", icon: DollarSign, label: "Add Expense" },
    { path: "/manage-users", icon: UserCog, label: "Manage Users" },
    { path: "/manage-groups", icon: FolderOpen, label: "Manage Groups" },
    { path: "/manage-expenses", icon: Receipt, label: "Manage Expenses" },
    { path: "/group-balances", icon: BarChart3, label: "Group Balances" },
    { path: "/user-balances", icon: BarChart3, label: "User Balances" },
    { path: "/settlements", icon: ArrowRightLeft, label: "Settlements" },
    { path: "/statistics", icon: TrendingUp, label: "Statistics" },
  ];

  return (
    <nav className="bg-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between">
          <div className="flex space-x-8">
            <div className="flex items-center py-6">
              <DollarSign className="h-8 w-8 text-blue-500" />
              <span className="ml-2 text-xl font-bold text-gray-900">
                Splitwise
              </span>
            </div>
            <div className="hidden md:flex items-center space-x-1">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`px-3 py-2 rounded-md text-sm font-medium flex items-center space-x-1 ${
                      isActive
                        ? "bg-blue-100 text-blue-700"
                        : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    <span>{item.label}</span>
                  </Link>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
};

const App: React.FC = () => {
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        await apiService.healthCheck();
        setIsHealthy(true);
      } catch (error) {
        setIsHealthy(false);
        console.error("Health check failed:", error);
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30000); // Check every 30 seconds
    return () => clearInterval(interval);
  }, []);

  if (isHealthy === false) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full">
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-red-100">
              <DollarSign className="h-6 w-6 text-red-600" />
            </div>
            <h3 className="mt-2 text-sm font-medium text-gray-900">
              Backend Unavailable
            </h3>
            <p className="mt-1 text-sm text-gray-500">
              Unable to connect to the Splitwise backend. Please ensure the
              backend service is running.
            </p>
            <div className="mt-6">
              <button
                onClick={() => window.location.reload()}
                className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
              >
                Retry Connection
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (isHealthy === null) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/create-user" element={<CreateUser />} />
            <Route path="/create-group" element={<CreateGroup />} />
            <Route path="/add-expense" element={<AddExpense />} />
            <Route path="/manage-users" element={<ManageUsers />} />
            <Route path="/manage-groups" element={<ManageGroups />} />
            <Route path="/manage-expenses" element={<ManageExpenses />} />
            <Route path="/group-balances" element={<GroupBalances />} />
            <Route path="/user-balances" element={<UserBalances />} />
            <Route path="/settlements" element={<Settlements />} />
            <Route path="/statistics" element={<ExpenseStatistics />} />
          </Routes>
        </main>
        <Chatbot />
      </div>
    </Router>
  );
};

export default App;
