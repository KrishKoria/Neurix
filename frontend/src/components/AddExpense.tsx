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
  const [groups, setGroups] = useState<Group[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<Group | null>(null);
  const [selectedGroupId, setSelectedGroupId] = useState("");
  const [description, setDescription] = useState("");
  const [amount, setAmount] = useState("");
  const [paidBy, setPaidBy] = useState("");
  const [splitType, setSplitType] = useState<"equal" | "percentage">("equal");
  const [percentageSplits, setPercentageSplits] = useState<{
    [userId: number]: number;
  }>({});
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [usersData, groupsData] = await Promise.all([
          apiService.getUsers(),
          apiService.getAllGroups(),
        ]);
        setUsers(usersData);
        setGroups(groupsData);

        // Check if groupId is in URL params
        const urlParams = new URLSearchParams(window.location.search);
        const groupIdFromUrl = urlParams.get("groupId");
        if (groupIdFromUrl) {
          setSelectedGroupId(groupIdFromUrl);
          const group = groupsData.find(
            (g) => g.id === parseInt(groupIdFromUrl)
          );
          if (group) {
            setSelectedGroup(group);
            initializePercentageSplits(group);
          }
        }
      } catch (error) {
        setMessage({ type: "error", text: "Failed to load data" });
      } finally {
        setLoadingData(false);
      }
    };

    loadData();
  }, []);

  const initializePercentageSplits = (group: Group) => {
    const equalPercentage = 100 / (group.users?.length || 1);
    const initialSplits: { [userId: number]: number } = {};
    group.users?.forEach((user) => {
      initialSplits[user.id] = equalPercentage;
    });
    setPercentageSplits(initialSplits);
  };

  const handleGroupChange = (groupId: string) => {
    setSelectedGroupId(groupId);
    setPaidBy("");
    setMessage(null);

    if (groupId) {
      const group = groups.find((g) => g.id === parseInt(groupId));
      if (group) {
        setSelectedGroup(group);
        initializePercentageSplits(group);
      }
    } else {
      setSelectedGroup(null);
      setPercentageSplits({});
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
        expense.splits =
          selectedGroup.users?.map((user) => ({
            user_id: user.id,
            percentage: percentageSplits[user.id] || 0,
          })) || [];
      }

      await apiService.createExpense(selectedGroup.id, expense);
      setMessage({ type: "success", text: "Expense added successfully!" });
      setDescription("");
      setAmount("");
      setPaidBy("");
      setSplitType("equal");
      if (selectedGroup) {
        initializePercentageSplits(selectedGroup);
      }
    } catch (error: any) {
      setMessage({
        type: "error",
        text: error.response?.data?.detail || "Failed to add expense",
      });
    } finally {
      setLoading(false);
    }
  };

  if (loadingData) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (groups.length === 0) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="bg-white shadow rounded-lg p-6 text-center">
          <Receipt className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No Groups Available
          </h3>
          <p className="text-gray-500 mb-4">
            You need to create a group first before adding expenses.
          </p>
          <a
            href="/create-group"
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
          >
            Create Your First Group
          </a>
        </div>
      </div>
    );
  }

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
                htmlFor="group"
                className="block text-sm font-medium text-gray-700"
              >
                Select Group
              </label>
              <select
                id="group"
                value={selectedGroupId}
                onChange={(e) => handleGroupChange(e.target.value)}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm px-3 py-2 border"
                disabled={loading}
              >
                <option value="">Choose a group</option>
                {groups.map((group) => (
                  <option key={group.id} value={group.id}>
                    {group.name} (ID: {group.id}) - {group.users?.length || 0}{" "}
                    members
                  </option>
                ))}
              </select>
            </div>

            {selectedGroup && (
              <div className="bg-gray-50 rounded-md p-3">
                <h4 className="text-sm font-medium text-gray-900 mb-2">
                  Group: {selectedGroup.name}
                </h4>
                <div className="flex flex-wrap gap-2">
                  {selectedGroup.users?.map((user) => (
                    <span
                      key={user.id}
                      className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                    >
                      {user.name} (ID: {user.id})
                    </span>
                  )) || (
                    <span className="text-sm text-gray-500">No members</span>
                  )}
                </div>
              </div>
            )}

            <div>
              <label
                htmlFor="description"
                className="block text-sm font-medium text-gray-700"
              >
                Description
              </label>
              <input
                type="text"
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm px-3 py-2 border"
                placeholder="What was this expense for?"
                disabled={loading}
              />
            </div>

            <div>
              <label
                htmlFor="amount"
                className="block text-sm font-medium text-gray-700"
              >
                Amount ($)
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

            {selectedGroup && selectedGroup.users && (
              <div>
                <label
                  htmlFor="paidBy"
                  className="block text-sm font-medium text-gray-700"
                >
                  Paid By
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
                    Equal split
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
                    Percentage split
                  </span>
                </label>
              </div>
            </div>

            {splitType === "percentage" &&
              selectedGroup &&
              selectedGroup.users && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Percentage Distribution (Total:{" "}
                    {getTotalPercentage().toFixed(1)}%)
                  </label>
                  <div className="space-y-3">
                    {selectedGroup.users.map((user) => (
                      <div
                        key={user.id}
                        className="flex items-center space-x-3"
                      >
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
