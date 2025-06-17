import React, { useState, useEffect } from "react";
import { Receipt, CheckCircle, AlertCircle } from "lucide-react";
import {
  apiService,
  type User,
  type Group,
  type ExpenseCreate,
} from "../lib/api";

const AddExpense: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<Group | null>(null);
  const [groupId, setGroupId] = useState("");
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [paidBy, setPaidBy] = useState("");
  const [splitType, setSplitType] = useState<"equal" | "percentage">("equal");
  const [percentageSplits, setPercentageSplits] = useState<{
    [userId: number]: number;
  }>({});
  const [loading, setLoading] = useState(false);
  const [loadingGroup, setLoadingGroup] = useState(false);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  useEffect(() => {
    const loadUsers = async () => {
      try {
        const usersData = await apiService.getUsers();
        setUsers(usersData);
      } catch (error) {
        console.error("Failed to load users:", error);
      }
    };

    loadUsers();
  }, []);

  const handleGroupIdChange = async (value: string) => {
    setGroupId(value);
    setSelectedGroup(null);
    setPaidBy("");
    setPercentageSplits({});

    if (value) {
      setLoadingGroup(true);
      try {
        const group = await apiService.getGroup(parseInt(value));
        setSelectedGroup(group);
        // Initialize percentage splits with equal distribution
        const equalPercentage = 100 / group.users.length;
        const initialSplits: { [userId: number]: number } = {};
        group.users.forEach((user) => {
          initialSplits[user.id] = equalPercentage;
        });
        setPercentageSplits(initialSplits);
      } catch (error: any) {
        setMessage({
          type: "error",
          text: error.response?.data?.detail || "Failed to load group",
        });
      } finally {
        setLoadingGroup(false);
      }
    }
  };

  const handlePercentageChange = (userId: number, percentage: number) => {
    setPercentageSplits((prev) => ({
      ...prev,
      [userId]: percentage,
    }));
  };

  const getTotalPercentage = () => {
    return Object.values(percentageSplits).reduce(
      (sum, percentage) => sum + percentage,
      0
    );
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!selectedGroup || !description.trim() || !amount || !paidBy) {
      setMessage({ type: "error", text: "Please fill in all required fields" });
      return;
    }

    const amountNum = parseFloat(amount);
    if (isNaN(amountNum) || amountNum <= 0) {
      setMessage({ type: "error", text: "Please enter a valid amount" });
      return;
    }

    if (splitType === "percentage") {
      const totalPercentage = getTotalPercentage();
      if (Math.abs(totalPercentage - 100) > 0.01) {
        setMessage({
          type: "error",
          text: `Percentages must sum to 100% (currently ${totalPercentage.toFixed(
            1
          )}%)`,
        });
        return;
      }
    }

    setLoading(true);
    setMessage(null);

    try {
      const expense: ExpenseCreate = {
        description: description.trim(),
        amount: amountNum,
        paid_by: parseInt(paidBy),
        split_type: splitType,
      };

      if (splitType === "percentage") {
        expense.splits = selectedGroup.users.map((user) => ({
          user_id: user.id,
          percentage: percentageSplits[user.id] || 0,
        }));
      }

      await apiService.createExpense(selectedGroup.id, expense);
      setMessage({ type: "success", text: "Expense added successfully!" });
      setDescription("");
      setAmount("");
      setPaidBy("");
      setSplitType("equal");
      // Reset percentage splits
      const equalPercentage = 100 / selectedGroup.users.length;
      const resetSplits: { [userId: number]: number } = {};
      selectedGroup.users.forEach((user) => {
        resetSplits[user.id] = equalPercentage;
      });
      setPercentageSplits(resetSplits);
    } catch (error: any) {
      setMessage({
        type: "error",
        text: error.response?.data?.detail || "Failed to add expense",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex items-center mb-4">
            <Receipt className="h-6 w-6 text-blue-500 mr-2" />
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Add New Expense
            </h3>
          </div>

          <div className="mb-6 p-4 bg-blue-50 rounded-lg">
            <h4 className="text-sm font-medium text-blue-900 mb-2">
              💡 Need Group ID?
            </h4>
            <p className="text-sm text-blue-700 mb-2">
              Don't know your Group ID? Check the Dashboard or Create Group page
              to see all group IDs.
            </p>
            <p className="text-xs text-blue-600">
              Group IDs are shown when you create a group or you can find them
              on the Dashboard.
            </p>
          </div>

          {message && (
            <div
              className={`mb-4 p-4 rounded-md ${
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

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label
                htmlFor="groupId"
                className="block text-sm font-medium text-gray-700"
              >
                Group ID <span className="text-red-500">*</span>
              </label>
              <div className="mt-1 relative">
                <input
                  type="number"
                  id="groupId"
                  value={groupId}
                  onChange={(e) => handleGroupIdChange(e.target.value)}
                  className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm px-3 py-2 border pr-10"
                  placeholder="Enter group ID (e.g., 1, 2, 3...)"
                  disabled={loading}
                />
                <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                  {loadingGroup && (
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                  )}
                </div>
              </div>
              {loadingGroup && (
                <p className="mt-1 text-sm text-gray-500">Loading group...</p>
              )}
            </div>

            {selectedGroup && (
              <div className="bg-green-50 border border-green-200 rounded-md p-4">
                <div className="flex items-center mb-2">
                  <CheckCircle className="h-5 w-5 text-green-500 mr-2" />
                  <h4 className="text-sm font-medium text-green-900">
                    Group Found!
                  </h4>
                </div>
                <div className="space-y-2">
                  <p className="text-sm text-green-800">
                    <strong>Group:</strong> {selectedGroup.name} (ID:{" "}
                    {selectedGroup.id})
                  </p>
                  <div>
                    <p className="text-sm text-green-800 mb-1">
                      <strong>Members:</strong>
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {selectedGroup.users.map((user) => (
                        <span
                          key={user.id}
                          className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"
                        >
                          {user.name} (ID: {user.id})
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div>
              <label
                htmlFor="description"
                className="block text-sm font-medium text-gray-700"
              >
                Description <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm px-3 py-2 border"
                placeholder="What was this expense for? (e.g., Dinner, Groceries, Movie tickets)"
                disabled={loading}
              />
            </div>

            <div>
              <label
                htmlFor="amount"
                className="block text-sm font-medium text-gray-700"
              >
                Amount ($) <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                step="0.01"
                id="amount"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm px-3 py-2 border"
                placeholder="0.00"
                disabled={loading}
              />
            </div>

            {selectedGroup && (
              <div>
                <label
                  htmlFor="paidBy"
                  className="block text-sm font-medium text-gray-700"
                >
                  Paid By <span className="text-red-500">*</span>
                </label>
                <select
                  id="paidBy"
                  value={paidBy}
                  onChange={(e) => setPaidBy(e.target.value)}
                  className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm px-3 py-2 border"
                  disabled={loading}
                >
                  <option value="">Select who paid</option>
                  {selectedGroup.users.map((user) => (
                    <option key={user.id} value={user.id}>
                      {user.name} (ID: {user.id})
                    </option>
                  ))}
                </select>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Split Type
              </label>
              <div className="space-y-2">
                <label className="flex items-center">
                  <input
                    type="radio"
                    value="equal"
                    checked={splitType === "equal"}
                    onChange={(e) => setSplitType(e.target.value as "equal")}
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                    disabled={loading}
                  />
                  <span className="ml-2 text-sm text-gray-700">
                    Equal split (everyone pays the same amount)
                  </span>
                </label>
                <label className="flex items-center">
                  <input
                    type="radio"
                    value="percentage"
                    checked={splitType === "percentage"}
                    onChange={(e) =>
                      setSplitType(e.target.value as "percentage")
                    }
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                    disabled={loading}
                  />
                  <span className="ml-2 text-sm text-gray-700">
                    Percentage split (custom percentages for each person)
                  </span>
                </label>
              </div>
            </div>

            {splitType === "percentage" && selectedGroup && (
              <div className="bg-gray-50 rounded-lg p-4">
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Percentage Distribution (Total:{" "}
                  {getTotalPercentage().toFixed(1)}%)
                  {getTotalPercentage() !== 100 && (
                    <span className="text-red-600 ml-2">
                      ⚠️ Must equal 100%
                    </span>
                  )}
                </label>
                <div className="space-y-3">
                  {selectedGroup.users.map((user) => (
                    <div key={user.id} className="flex items-center space-x-3">
                      <div className="flex-1">
                        <span className="text-sm text-gray-700">
                          {user.name} (ID: {user.id})
                        </span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <input
                          type="number"
                          step="0.1"
                          min="0"
                          max="100"
                          value={percentageSplits[user.id] || 0}
                          onChange={(e) =>
                            handlePercentageChange(
                              user.id,
                              parseFloat(e.target.value) || 0
                            )
                          }
                          className="w-20 border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm px-2 py-1 border"
                          disabled={loading}
                        />
                        <span className="text-sm text-gray-500">%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <button
              type="submit"
              disabled={loading || !selectedGroup}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Adding..." : "Add Expense"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default AddExpense;
