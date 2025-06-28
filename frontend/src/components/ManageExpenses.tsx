import React, { useState, useEffect } from "react";
import { apiService, type Group, type GroupSummary, type Expense, type User } from "../lib/api";
import { Receipt, Search, Edit, Trash2, Plus, Eye, DollarSign } from "lucide-react";

const ManageExpenses = () => {
  const [groups, setGroups] = useState<GroupSummary[]>([]);
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedExpense, setSelectedExpense] = useState<Expense | null>(null);

  useEffect(() => {
    loadInitialData();
  }, []);

  useEffect(() => {
    if (selectedGroup) {
      loadGroupExpenses(selectedGroup);
    }
  }, [selectedGroup]);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      const [groupsData, usersData] = await Promise.all([
        apiService.getAllGroups(),
        apiService.getUsers()
      ]);
      setGroups(groupsData);
      setUsers(usersData);
      
      if (groupsData.length > 0) {
        setSelectedGroup(groupsData[0].id);
      }
    } catch (error) {
      console.error("Error loading initial data:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadGroupExpenses = async (groupId: number) => {
    try {
      const expensesData = await apiService.getGroupExpenses(groupId);
      setExpenses(expensesData);
    } catch (error) {
      console.error("Error loading group expenses:", error);
      setExpenses([]);
    }
  };

  const handleDeleteExpense = async (expenseId: number) => {
    if (!confirm("Are you sure you want to delete this expense?")) return;
    
    try {
      await apiService.deleteExpense(expenseId);
      if (selectedGroup) {
        loadGroupExpenses(selectedGroup);
      }
    } catch (error) {
      console.error("Error deleting expense:", error);
    }
  };

  const getUserName = (userId: number) => {
    const user = users.find(u => u.id === userId);
    return user ? user.name : `User ${userId}`;
  };

  const filteredExpenses = (expenses || []).filter((expense) =>
    expense.description.toLowerCase().includes(search.toLowerCase()) ||
    expense.paid_by_name.toLowerCase().includes(search.toLowerCase())
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
          <Receipt className="h-6 w-6 text-blue-500" />
          <h1 className="text-2xl font-bold text-gray-900">Manage Expenses</h1>
        </div>
      </div>

      {/* Group Selection */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select Group
        </label>
        <select
          value={selectedGroup || ""}
          onChange={(e) => setSelectedGroup(Number(e.target.value))}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
        >
          <option value="">Select a group...</option>
          {(groups || []).map((group) => (
            <option key={group.id} value={group.id}>
              {group.name} (${group.total_expenses.toFixed(2)})
            </option>
          ))}
        </select>
      </div>

      {selectedGroup && (
        <>
          {/* Search */}
          <div className="mb-6">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search expenses by description or paid by..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          {/* Expenses List */}
          <div className="bg-white shadow overflow-hidden sm:rounded-md">
            <ul className="divide-y divide-gray-200">
              {filteredExpenses.map((expense) => (
                <li key={expense.id} className="px-6 py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <div className="h-10 w-10 rounded-full bg-green-500 flex items-center justify-center">
                          <DollarSign className="h-5 w-5 text-white" />
                        </div>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">
                          {expense.description}
                        </div>
                        <div className="text-sm text-gray-500">
                          Paid by: {expense.paid_by_name}
                        </div>
                        <div className="text-xs text-gray-400">
                          {new Date(expense.created_at).toLocaleDateString()} • 
                          Split: {expense.split_type}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-4">
                      <div className="text-right">
                        <div className="text-lg font-semibold text-gray-900">
                          ${expense.amount.toFixed(2)}
                        </div>
                        <div className="text-xs text-gray-500">
                          {(expense.splits || []).length} split{(expense.splits || []).length !== 1 ? 's' : ''}
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => setSelectedExpense(expense)}
                          className="p-2 text-gray-400 hover:text-blue-500"
                          title="View Details"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                        <button
                          onClick={() => handleDeleteExpense(expense.id)}
                          className="p-2 text-gray-400 hover:text-red-500"
                          title="Delete Expense"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </div>
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </div>

          {filteredExpenses.length === 0 && (
            <div className="text-center py-8">
              <Receipt className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">No expenses found</h3>
              <p className="mt-1 text-sm text-gray-500">
                {search ? "Try adjusting your search terms." : "No expenses have been added to this group yet."}
              </p>
            </div>
          )}
        </>
      )}

      {!selectedGroup && groups.length === 0 && (
        <div className="text-center py-8">
          <Receipt className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No groups available</h3>
          <p className="mt-1 text-sm text-gray-500">
            Create a group first before managing expenses.
          </p>
        </div>
      )}

      {/* Expense Details Modal */}
      {selectedExpense && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
          <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
            <h3 className="text-lg font-bold text-gray-900 mb-4">Expense Details</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700">Description</label>
                <p className="text-sm text-gray-900">{selectedExpense.description}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Amount</label>
                <p className="text-sm text-gray-900">${selectedExpense.amount.toFixed(2)}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Paid By</label>
                <p className="text-sm text-gray-900">{selectedExpense.paid_by_name}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Split Type</label>
                <p className="text-sm text-gray-900">{selectedExpense.split_type}</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Splits</label>
                <div className="space-y-1">
                  {(selectedExpense.splits || []).map((split, index) => (
                    <div key={index} className="flex justify-between">
                      <span className="text-sm text-gray-900">{split.user_name}</span>
                      <span className="text-sm text-gray-900">
                        ${split.amount.toFixed(2)}
                        {split.percentage && ` (${split.percentage}%)`}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Created</label>
                <p className="text-sm text-gray-900">
                  {new Date(selectedExpense.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>
            <div className="flex justify-end mt-4">
              <button
                onClick={() => setSelectedExpense(null)}
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

export default ManageExpenses;
