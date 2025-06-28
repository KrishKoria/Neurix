import React, { useState, useEffect } from "react";
import {
  Users,
  UserPlus,
  Receipt,
  TrendingUp,
  Eye,
  Copy,
  Check,
} from "lucide-react";
import { apiService, type User, type GroupSummary } from "../lib/api";

const Dashboard: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [groups, setGroups] = useState<GroupSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [usersData, groupsData] = await Promise.all([
          apiService.getUsers(),
          apiService.getAllGroups(),
        ]);
        setUsers(usersData);
        setGroups(groupsData);
      } catch (error) {
        console.error("Error loading dashboard data:", error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const copyToClipboard = async (text: string, type: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(`${type}-${text}`);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (error) {
      console.error("Failed to copy to clipboard:", error);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="px-4 py-6 sm:px-0">
      <div className="border-4 border-dashed border-gray-200 rounded-lg p-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Welcome to Splitwise
          </h1>
          <p className="text-lg text-gray-600">
            Manage shared expenses and track balances with friends
          </p>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Users className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Total Users
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {users.length}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <UserPlus className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Active Groups
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {groups.length}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Receipt className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Total Expenses
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {groups
                        .reduce(
                          (sum, group) => sum + (group.total_expenses || 0),
                          0
                        )
                        .toFixed(0)}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <TrendingUp className="h-6 w-6 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Total Amount
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      $
                      {groups
                        .reduce(
                          (sum, group) => sum + (group.total_expenses || 0),
                          0
                        )
                        .toFixed(2)}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Users Section */}
        <div className="bg-white shadow rounded-lg mb-8">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Users Directory
            </h3>
            {users.length === 0 ? (
              <p className="text-gray-500">
                No users created yet. Start by creating some users!
              </p>
            ) : (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        User ID
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Name
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Email
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Groups
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {users.map((user) => {
                      // Note: Group membership display temporarily disabled
                      // since we're using GroupSummary which doesn't include user details

                      return (
                        <tr key={user.id}>
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                            <div className="flex items-center space-x-2">
                              <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs font-semibold">
                                ID: {user.id}
                              </span>
                              <button
                                onClick={() =>
                                  copyToClipboard(user.id.toString(), "user")
                                }
                                className="text-gray-400 hover:text-gray-600"
                                title="Copy User ID"
                              >
                                {copiedId === `user-${user.id}` ? (
                                  <Check className="h-4 w-4 text-green-500" />
                                ) : (
                                  <Copy className="h-4 w-4" />
                                )}
                              </button>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex items-center">
                              <div className="h-8 w-8 rounded-full bg-blue-500 flex items-center justify-center mr-3">
                                <span className="text-sm font-medium text-white">
                                  {user.name.charAt(0).toUpperCase()}
                                </span>
                              </div>
                              <span className="text-sm font-medium text-gray-900">
                                {user.name}
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {user.email}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <div className="flex flex-wrap gap-1">
                              <span className="text-xs text-gray-400">
                                Group membership info not available
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            <button
                              onClick={() =>
                                window.open(
                                  `/user-balances?userId=${user.id}`,
                                  "_blank"
                                )
                              }
                              className="text-blue-600 hover:text-blue-900 flex items-center"
                            >
                              <Eye className="h-4 w-4 mr-1" />
                              View Balances
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* Groups Section */}
        <div className="bg-white shadow rounded-lg">
          <div className="px-4 py-5 sm:p-6">
            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
              Groups Directory
            </h3>
            {groups.length === 0 ? (
              <p className="text-gray-500">
                No groups created yet. Create a group to start splitting
                expenses!
              </p>
            ) : (
              <div className="grid gap-4">
                {groups.map((group) => (
                  <div
                    key={group.id}
                    className="border border-gray-200 rounded-lg p-4"
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        <div className="h-10 w-10 rounded-full bg-purple-500 flex items-center justify-center">
                          <span className="text-sm font-medium text-white">
                            {group.name.charAt(0).toUpperCase()}
                          </span>
                        </div>
                        <div>
                          <h4 className="text-lg font-medium text-gray-900">
                            {group.name}
                          </h4>
                          <div className="flex items-center space-x-2">
                            <span className="bg-purple-100 text-purple-800 px-2 py-1 rounded-full text-xs font-semibold">
                              ID: {group.id}
                            </span>
                            <button
                              onClick={() =>
                                copyToClipboard(group.id.toString(), "group")
                              }
                              className="text-gray-400 hover:text-gray-600"
                              title="Copy Group ID"
                            >
                              {copiedId === `group-${group.id}` ? (
                                <Check className="h-4 w-4 text-green-500" />
                              ) : (
                                <Copy className="h-4 w-4" />
                              )}
                            </button>
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-gray-500">Total Expenses</p>
                        <p className="text-lg font-semibold text-gray-900">
                          ${(group.total_expenses || 0).toFixed(2)}
                        </p>
                      </div>
                    </div>

                    <div className="mb-3">
                      <p className="text-sm text-gray-500 mb-2">
                        Members ({group.member_count || 0}):
                      </p>
                      <div className="flex flex-wrap gap-2">
                        <span className="text-xs text-gray-400">
                          Member details not available in summary view
                        </span>
                      </div>
                    </div>

                    <div className="flex space-x-2">
                      <button
                        onClick={() =>
                          window.open(
                            `/add-expense?groupId=${group.id}`,
                            "_blank"
                          )
                        }
                        className="flex-1 bg-blue-600 text-white px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700"
                      >
                        Add Expense
                      </button>
                      <button
                        onClick={() =>
                          window.open(
                            `/group-balances?groupId=${group.id}`,
                            "_blank"
                          )
                        }
                        className="flex-1 bg-gray-600 text-white px-3 py-2 rounded-md text-sm font-medium hover:bg-gray-700"
                      >
                        View Balances
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
