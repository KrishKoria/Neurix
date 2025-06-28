import React, { useState, useEffect } from "react";
import { BarChart3, CheckCircle, AlertCircle } from "lucide-react";
import { apiService, type Balance, type Group, type GroupSummary } from "../lib/api";

const GroupBalances: React.FC = () => {
  const [groups, setGroups] = useState<GroupSummary[]>([]);
  const [selectedGroupId, setSelectedGroupId] = useState("");
  const [selectedGroupDetails, setSelectedGroupDetails] = useState<Group | null>(null);
  const [balances, setBalances] = useState<Balance[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingData, setLoadingData] = useState(true);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const groupsData = await apiService.getAllGroups();
        setGroups(groupsData);

        // Check if groupId is in URL params
        const urlParams = new URLSearchParams(window.location.search);
        const groupIdFromUrl = urlParams.get("groupId");
        if (groupIdFromUrl) {
          setSelectedGroupId(groupIdFromUrl);
          await handleSearch(groupIdFromUrl);
        }
      } catch (error) {
        setMessage({ type: "error", text: "Failed to load groups" });
      } finally {
        setLoadingData(false);
      }
    };

    loadData();
  }, []);

  useEffect(() => {
    const fetchGroupDetails = async () => {
      if (selectedGroupId) {
        try {
          const groupDetails = await apiService.getGroup(parseInt(selectedGroupId));
          setSelectedGroupDetails(groupDetails);
        } catch (error) {
          console.error("Error fetching group details:", error);
          setSelectedGroupDetails(null);
        }
      } else {
        setSelectedGroupDetails(null);
      }
    };

    fetchGroupDetails();
  }, [selectedGroupId]);

  const handleSearch = async (groupId?: string) => {
    const targetGroupId = groupId || selectedGroupId;

    if (!targetGroupId) {
      setMessage({ type: "error", text: "Please select a group" });
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      const balancesData = await apiService.getGroupBalances(
        parseInt(targetGroupId)
      );
      setBalances(balancesData);
      if (balancesData.length === 0) {
        setMessage({ type: "error", text: "No balances found for this group" });
      }
    } catch (error: any) {
      setMessage({
        type: "error",
        text: error.response?.data?.detail || "Failed to load group balances",
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
        text: `is owed $${absBalance.toFixed(2)}`,
        color: "text-green-600",
        bgColor: "bg-green-50",
      };
    } else if (balance < 0) {
      return {
        text: `owes $${absBalance.toFixed(2)}`,
        color: "text-red-600",
        bgColor: "bg-red-50",
      };
    } else {
      return {
        text: "is settled up",
        color: "text-gray-600",
        bgColor: "bg-gray-50",
      };
    }
  };

  const selectedGroup = groups.find((g) => g.id === parseInt(selectedGroupId));

  if (loadingData) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (groups.length === 0) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-white shadow rounded-lg p-6 text-center">
          <BarChart3 className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            No Groups Available
          </h3>
          <p className="text-gray-500 mb-4">
            You need to create a group first before viewing balances.
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
    <div className="max-w-4xl mx-auto">
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex items-center mb-6">
            <BarChart3 className="h-6 w-6 text-blue-500 mr-2" />
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Group Balances
            </h3>
          </div>

          <div className="mb-6">
            <div className="flex space-x-3">
              <div className="flex-1">
                <label htmlFor="groupSelect" className="sr-only">
                  Select Group
                </label>
                <select
                  id="groupSelect"
                  value={selectedGroupId}
                  onChange={(e) => setSelectedGroupId(e.target.value)}
                  className="block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm px-3 py-2 border"
                  disabled={loading}
                >
                  <option value="">Select a group</option>
                  {groups.map((group) => (
                    <option key={group.id} value={group.id}>
                      {group.name} (ID: {group.id}) - {group.member_count || 0}{" "}
                      members
                    </option>
                  ))}
                </select>
              </div>
              <button
                onClick={() => handleSearch()}
                disabled={loading || !selectedGroupId}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                {loading ? "Loading..." : "Get Balances"}
              </button>
            </div>
          </div>

          {selectedGroupDetails && (
            <div className="mb-6 bg-gray-50 rounded-md p-4">
              <h4 className="text-sm font-medium text-gray-900 mb-2">
                Selected Group: {selectedGroupDetails.name}
              </h4>
              <div className="flex flex-wrap gap-2">
                {selectedGroupDetails.users?.map((user) => (
                  <span
                    key={user.id}
                    className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                  >
                    {user.name}
                  </span>
                )) || <span className="text-sm text-gray-500">No members</span>}
              </div>
            </div>
          )}

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
              <h4 className="text-lg font-medium text-gray-900 mb-4">
                Balance Summary for {selectedGroupDetails?.name}
              </h4>
              <div className="grid gap-4">
                {balances.map((balance) => {
                  const { text, color, bgColor } = formatBalance(
                    balance.balance
                  );
                  return (
                    <div
                      key={balance.user_id}
                      className={`rounded-lg border p-4 ${bgColor}`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className="flex-shrink-0">
                            <div className="h-10 w-10 rounded-full bg-blue-500 flex items-center justify-center">
                              <span className="text-sm font-medium text-white">
                                {balance.user_name.charAt(0).toUpperCase()}
                              </span>
                            </div>
                          </div>
                          <div>
                            <p className="text-lg font-medium text-gray-900">
                              {balance.user_name}
                            </p>
                            <p className={`text-sm ${color}`}>{text}</p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className={`text-2xl font-bold ${color}`}>
                            ${Math.abs(balance.balance).toFixed(2)}
                          </p>
                          <p className="text-sm text-gray-500">
                            {balance.balance > 0
                              ? "Credit"
                              : balance.balance < 0
                              ? "Debit"
                              : "Even"}
                          </p>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                <h5 className="text-sm font-medium text-blue-900 mb-2">
                  Understanding Balances:
                </h5>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>
                    • <strong>Positive balance (Green):</strong> This person is
                    owed money
                  </li>
                  <li>
                    • <strong>Negative balance (Red):</strong> This person owes
                    money
                  </li>
                  <li>
                    • <strong>Zero balance (Gray):</strong> This person is
                    settled up
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

export default GroupBalances;
