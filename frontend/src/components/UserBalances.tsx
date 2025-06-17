import React, { useState } from "react";
import { User, CheckCircle, AlertCircle, Search } from "lucide-react";
import { apiService, type UserBalance } from "../lib/api";

const UserBalances: React.FC = () => {
  const [userId, setUserId] = useState("");
  const [balances, setBalances] = useState<UserBalance[]>([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  const handleSearch = async () => {
    if (!userId) {
      setMessage({ type: "error", text: "Please enter a user ID" });
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      const balancesData = await apiService.getUserBalances(parseInt(userId));
      setBalances(balancesData);
      if (balancesData.length === 0) {
        setMessage({ type: "error", text: "No balances found for this user" });
      }
    } catch (error: any) {
      setMessage({
        type: "error",
        text: error.response?.data?.detail || "Failed to load user balances",
      });
      setBalances([]);
    } finally {
      setLoading(false);
    }
  };

  const formatBalance = (balance: number) => {
    const absBalance = Math.abs(balance);
    if (balance > 0) {
      return {
        text: `+$${absBalance.toFixed(2)}`,
        color: "text-green-600",
        bgColor: "bg-green-50",
        label: "You are owed",
      };
    } else if (balance < 0) {
      return {
        text: `-$${absBalance.toFixed(2)}`,
        color: "text-red-600",
        bgColor: "bg-red-50",
        label: "You owe",
      };
    } else {
      return {
        text: "$0.00",
        color: "text-gray-600",
        bgColor: "bg-gray-50",
        label: "Settled up",
      };
    }
  };

  const getTotalBalance = () => {
    return balances.reduce((sum, balance) => sum + balance.balance, 0);
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex items-center mb-6">
            <User className="h-6 w-6 text-blue-500 mr-2" />
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              User Balance Summary
            </h3>
          </div>

          <div className="mb-6">
            <div className="flex space-x-3">
              <div className="flex-1">
                <label htmlFor="userId" className="sr-only">
                  User ID
                </label>
                <input
                  type="number"
                  id="userId"
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm px-3 py-2 border"
                  placeholder="Enter user ID"
                  disabled={loading}
                />
              </div>
              <button
                onClick={handleSearch}
                disabled={loading}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                <Search className="h-4 w-4 mr-2" />
                {loading ? "Loading..." : "Get Balances"}
              </button>
            </div>
          </div>

          {message && (
            <div
              className={`mb-6 p-4 rounded-md ${
                message.type === "success"
                  ? "bg-green-50 text-green-700"
                  : "bg-red-50 text-red-700"
              }`}
            >
              <div className="flex">
                <div className="flex-shrink-0">
                  {message.type === "success" ? (
                    <CheckCircle className="h-5 w-5" />
                  ) : (
                    <AlertCircle className="h-5 w-5" />
                  )}
                </div>
                <div className="ml-3">
                  <p className="text-sm">{message.text}</p>
                </div>
              </div>
            </div>
          )}

          {balances.length > 0 && (
            <div>
              <div className="mb-6">
                <div className="bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg p-6 text-white">
                  <h4 className="text-xl font-semibold mb-2">
                    Overall Balance for User {userId}
                  </h4>
                  <div className="flex items-center justify-between">
                    <span className="text-blue-100">
                      Total across all groups:
                    </span>
                    <span
                      className={`text-3xl font-bold ${
                        getTotalBalance() >= 0
                          ? "text-green-300"
                          : "text-red-300"
                      }`}
                    >
                      {getTotalBalance() >= 0 ? "+" : ""}$
                      {getTotalBalance().toFixed(2)}
                    </span>
                  </div>
                </div>
              </div>

              <h4 className="text-lg font-medium text-gray-900 mb-4">
                Balance by Group
              </h4>
              <div className="grid gap-4">
                {balances.map((balance) => {
                  const { text, color, bgColor, label } = formatBalance(
                    balance.balance
                  );
                  return (
                    <div
                      key={balance.group_id}
                      className={`rounded-lg border p-4 ${bgColor}`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className="flex-shrink-0">
                            <div className="h-10 w-10 rounded-full bg-blue-500 flex items-center justify-center">
                              <span className="text-sm font-medium text-white">
                                {balance.group_name.charAt(0).toUpperCase()}
                              </span>
                            </div>
                          </div>
                          <div>
                            <p className="text-lg font-medium text-gray-900">
                              {balance.group_name}
                            </p>
                            <p className={`text-sm ${color}`}>{label}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className={`text-2xl font-bold ${color}`}>
                            {text}
                          </p>
                          <p className="text-sm text-gray-500">
                            Group ID: {balance.group_id}
                          </p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                <h5 className="text-sm font-medium text-blue-900 mb-2">
                  Understanding Your Balances:
                </h5>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>
                    • <strong>Positive balance (Green):</strong> You are owed
                    money in this group
                  </li>
                  <li>
                    • <strong>Negative balance (Red):</strong> You owe money in
                    this group
                  </li>
                  <li>
                    • <strong>Zero balance (Gray):</strong> You are settled up
                    in this group
                  </li>
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserBalances;
