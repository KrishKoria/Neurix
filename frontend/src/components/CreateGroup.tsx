import React, { useState, useEffect } from "react";
import { Users, CheckCircle, AlertCircle, Copy, Check } from "lucide-react";
import { apiService, type User, type Group } from "../lib/api";

const CreateGroup: React.FC = () => {
  const [groupName, setGroupName] = useState("");
  const [users, setUsers] = useState<User[]>([]);
  const [selectedUsers, setSelectedUsers] = useState<number[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingUsers, setLoadingUsers] = useState(true);
  const [message, setMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);
  const [createdGroup, setCreatedGroup] = useState<Group | null>(null);
  const [copiedId, setCopiedId] = useState<number | null>(null);

  useEffect(() => {
    const loadUsers = async () => {
      try {
        const usersData = await apiService.getUsers();
        setUsers(usersData);
      } catch (error) {
        setMessage({ type: "error", text: "Failed to load users" });
      } finally {
        setLoadingUsers(false);
      }
    };

    loadUsers();
  }, []);

  const handleUserToggle = (userId: number) => {
    setSelectedUsers((prev) =>
      prev.includes(userId)
        ? prev.filter((id) => id !== userId)
        : [...prev, userId]
    );
  };

  const copyToClipboard = async (id: number) => {
    try {
      await navigator.clipboard.writeText(id.toString());
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      console.error("Failed to copy ID:", err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!groupName.trim()) {
      setMessage({ type: "error", text: "Please enter a group name" });
      return;
    }
    if (selectedUsers.length < 2) {
      setMessage({ type: "error", text: "Please select at least 2 users" });
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      const group = await apiService.createGroup(
        groupName.trim(),
        selectedUsers
      );
      setCreatedGroup(group);
      setMessage({
        type: "success",
        text: `Group created successfully! Group ID: ${group.id}`,
      });
      setGroupName("");
      setSelectedUsers([]);
    } catch (error: any) {
      setMessage({
        type: "error",
        text: error.response?.data?.detail || "Failed to create group",
      });
    } finally {
      setLoading(false);
    }
  };

  if (loadingUsers) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto">
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex items-center mb-4">
            <Users className="h-6 w-6 text-blue-500 mr-2" />
            <h3 className="text-lg leading-6 font-medium text-gray-900">
              Create New Group
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

          {createdGroup && (
            <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
              <h4 className="text-sm font-medium text-blue-900 mb-3">
                ✅ Group Created Successfully!
              </h4>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-blue-700">Group ID:</span>
                  <div className="flex items-center space-x-2">
                    <span className="px-3 py-1 bg-blue-100 text-blue-900 rounded font-mono text-lg font-bold">
                      {createdGroup.id}
                    </span>
                    <button
                      onClick={() => copyToClipboard(createdGroup.id)}
                      className="text-blue-600 hover:text-blue-800"
                      title="Copy Group ID"
                    >
                      {copiedId === createdGroup.id ? (
                        <Check className="h-4 w-4 text-green-600" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-blue-700">Group Name:</span>
                  <span className="text-sm font-medium text-blue-900">
                    {createdGroup.name}
                  </span>
                </div>
                <div>
                  <span className="text-sm text-blue-700">Members:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {createdGroup.users.map((user) => (
                      <span
                        key={user.id}
                        className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                      >
                        {user.name} (ID: {user.id})
                      </span>
                    ))}
                  </div>
                </div>
                <div className="mt-3 p-2 bg-blue-100 rounded text-xs text-blue-800">
                  💡 <strong>Save this Group ID!</strong> You'll need it to add
                  expenses and check balances.
                </div>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label
                htmlFor="groupName"
                className="block text-sm font-medium text-gray-700"
              >
                Group Name
              </label>
              <input
                type="text"
                id="groupName"
                value={groupName}
                onChange={(e) => setGroupName(e.target.value)}
                className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm px-3 py-2 border"
                placeholder="Enter group name"
                disabled={loading}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Select Users ({selectedUsers.length} selected)
              </label>

              {users.length === 0 ? (
                <p className="text-gray-500">
                  No users available. Create some users first!
                </p>
              ) : (
                <div className="grid grid-cols-1 gap-3 max-h-60 overflow-y-auto">
                  {users.map((user) => (
                    <div
                      key={user.id}
                      onClick={() => handleUserToggle(user.id)}
                      className={`relative rounded-lg border cursor-pointer p-3 ${
                        selectedUsers.includes(user.id)
                          ? "border-blue-500 bg-blue-50"
                          : "border-gray-300 hover:border-gray-400"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-3">
                          <div className="flex-shrink-0">
                            <div
                              className={`h-8 w-8 rounded-full flex items-center justify-center ${
                                selectedUsers.includes(user.id)
                                  ? "bg-blue-500"
                                  : "bg-gray-400"
                              }`}
                            >
                              <span className="text-sm font-medium text-white">
                                {user.name.charAt(0).toUpperCase()}
                              </span>
                            </div>
                          </div>
                          <div className="min-w-0 flex-1">
                            <p className="text-sm font-medium text-gray-900">
                              {user.name}
                            </p>
                            <p className="text-sm text-gray-500">
                              {user.email}
                            </p>
                            <p className="text-xs text-gray-400">
                              ID: {user.id}
                            </p>
                          </div>
                        </div>
                        {selectedUsers.includes(user.id) && (
                          <CheckCircle className="h-5 w-5 text-blue-500" />
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <button
              type="submit"
              disabled={loading || users.length === 0}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Creating..." : "Create Group"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default CreateGroup;
