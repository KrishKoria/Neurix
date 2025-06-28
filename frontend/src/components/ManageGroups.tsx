import React, { useState, useEffect } from "react";
import {
  apiService,
  type Group,
  type GroupSummary,
  type User,
} from "../lib/api";
import {
  FolderPlus,
  Search,
  Edit,
  Trash2,
  Plus,
  Eye,
  Users,
} from "lucide-react";

const ManageGroups = () => {
  const [groups, setGroups] = useState<GroupSummary[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedGroup, setSelectedGroup] = useState<Group | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    selectedUserIds: [] as number[],
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [groupsData, usersData] = await Promise.all([
        apiService.getAllGroups(),
        apiService.getUsers(),
      ]);
      setGroups(groupsData);
      setUsers(usersData);
    } catch (error) {
      console.error("Error loading data:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiService.createGroup(formData.name, formData.selectedUserIds);
      setFormData({ name: "", selectedUserIds: [] });
      setShowCreateModal(false);
      loadData();
    } catch (error) {
      console.error("Error creating group:", error);
    }
  };

  const handleUpdateGroup = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedGroup) return;

    try {
      await apiService.updateGroup(
        selectedGroup.id,
        formData.name,
        formData.selectedUserIds
      );
      setFormData({ name: "", selectedUserIds: [] });
      setShowEditModal(false);
      setSelectedGroup(null);
      loadData();
    } catch (error) {
      console.error("Error updating group:", error);
    }
  };

  const handleDeleteGroup = async (groupId: number) => {
    if (!confirm("Are you sure you want to delete this group?")) return;

    try {
      await apiService.deleteGroup(groupId);
      loadData();
    } catch (error) {
      console.error("Error deleting group:", error);
    }
  };

  const openEditModal = async (groupSummary: GroupSummary) => {
    try {
      const fullGroup = await apiService.getGroup(groupSummary.id);
      setSelectedGroup(fullGroup);
      setFormData({
        name: fullGroup.name,
        selectedUserIds: (fullGroup.users || []).map((u) => u.id),
      });
      setShowEditModal(true);
    } catch (error) {
      console.error("Error loading group details:", error);
    }
  };

  const openViewModal = async (groupSummary: GroupSummary) => {
    try {
      const fullGroup = await apiService.getGroup(groupSummary.id);
      setSelectedGroup(fullGroup);
    } catch (error) {
      console.error("Error loading group details:", error);
    }
  };

  const toggleUserSelection = (userId: number) => {
    setFormData((prev) => ({
      ...prev,
      selectedUserIds: prev.selectedUserIds.includes(userId)
        ? prev.selectedUserIds.filter((id) => id !== userId)
        : [...prev.selectedUserIds, userId],
    }));
  };

  const handleViewGroup = async (groupId: number) => {
    try {
      const fullGroup = await apiService.getGroup(groupId);
      setSelectedGroup(fullGroup);
    } catch (error) {
      console.error("Error fetching group details:", error);
    }
  };

  const filteredGroups = (groups || []).filter((group) =>
    group.name.toLowerCase().includes(search.toLowerCase())
  );

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500 mx-auto"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center space-x-2">
          <FolderPlus className="h-6 w-6 text-blue-500" />
          <h1 className="text-2xl font-bold text-gray-900">Manage Groups</h1>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Group
        </button>
      </div>

      {/* Search */}
      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search groups by name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      {/* Groups Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredGroups.map((group) => (
          <div
            key={group.id}
            className="bg-white overflow-hidden shadow rounded-lg"
          >
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <FolderPlus className="h-8 w-8 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      {group.name}
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      ${group.total_expenses.toFixed(2)}
                    </dd>
                  </dl>
                </div>
              </div>
              <div className="mt-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <Users className="h-4 w-4 text-gray-400 mr-1" />
                    <span className="text-sm text-gray-500">
                      {group.member_count} member
                      {group.member_count !== 1 ? "s" : ""}
                    </span>
                  </div>
                  <div className="text-xs text-gray-400">
                    Group ID: {group.id}
                  </div>
                </div>
                <div className="mt-2 flex flex-wrap gap-1">
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                    {group.member_count} Members
                  </span>
                  {/* We'll show member names when viewing group details */}
                </div>
              </div>
              <div className="mt-4 flex justify-end space-x-2">
                <button
                  onClick={() => handleViewGroup(group.id)}
                  className="p-2 text-gray-400 hover:text-blue-500"
                  title="View Details"
                >
                  <Eye className="h-4 w-4" />
                </button>
                <button
                  onClick={() => openEditModal(group)}
                  className="p-2 text-gray-400 hover:text-blue-500"
                  title="Edit Group"
                >
                  <Edit className="h-4 w-4" />
                </button>
                <button
                  onClick={() => handleDeleteGroup(group.id)}
                  className="p-2 text-gray-400 hover:text-red-500"
                  title="Delete Group"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredGroups.length === 0 && (
        <div className="text-center py-8">
          <FolderPlus className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">
            No groups found
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            {search
              ? "Try adjusting your search terms."
              : "Get started by creating a new group."}
          </p>
        </div>
      )}

      {/* Create/Edit Group Modal */}
      {(showCreateModal || showEditModal) && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <h3 className="text-lg font-bold text-gray-900 mb-4">
              {showCreateModal ? "Create New Group" : "Edit Group"}
            </h3>
            <form
              onSubmit={showCreateModal ? handleCreateGroup : handleUpdateGroup}
            >
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Group Name
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) =>
                    setFormData({ ...formData, name: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Select Members
                </label>
                <div className="max-h-40 overflow-y-auto border border-gray-300 rounded-md p-2">
                  {(users || []).map((user) => (
                    <label
                      key={user.id}
                      className="flex items-center space-x-2 p-1"
                    >
                      <input
                        type="checkbox"
                        checked={formData.selectedUserIds.includes(user.id)}
                        onChange={() => toggleUserSelection(user.id)}
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <span className="text-sm">{user.name}</span>
                    </label>
                  ))}
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  Selected: {formData.selectedUserIds.length} user(s)
                </p>
              </div>

              <div className="flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setShowEditModal(false);
                    setSelectedGroup(null);
                    setFormData({ name: "", selectedUserIds: [] });
                  }}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
                >
                  {showCreateModal ? "Create Group" : "Update Group"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Group Details Modal */}
      {selectedGroup && !showEditModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <h3 className="text-lg font-bold text-gray-900 mb-4">
              Group Details
            </h3>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Name
                </label>
                <p className="text-sm text-gray-900">{selectedGroup.name}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Total Expenses
                </label>
                <p className="text-sm text-gray-900">
                  ${selectedGroup.total_expenses.toFixed(2)}
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Members
                </label>
                <div className="space-y-1">
                  {(selectedGroup.users || []).map((user) => (
                    <p key={user.id} className="text-sm text-gray-900">
                      {user.name}
                    </p>
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Created
                </label>
                <p className="text-sm text-gray-900">
                  {new Date(selectedGroup.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
            <div className="flex justify-end mt-4">
              <button
                onClick={() => setSelectedGroup(null)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ManageGroups;
