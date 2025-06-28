import React, { useState, useEffect } from "react";
import { apiService, type GroupSummary } from "../lib/api";
import { ArrowRightLeft, DollarSign } from "lucide-react";

interface Settlement {
  from_user: string;
  to_user: string;
  amount: number;
}

const Settlements = () => {
  const [groups, setGroups] = useState<GroupSummary[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<number | null>(null);
  const [settlements, setSettlements] = useState<Settlement[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingSettlements, setLoadingSettlements] = useState(false);

  useEffect(() => {
    loadGroups();
  }, []);

  useEffect(() => {
    if (selectedGroup) {
      loadSettlements(selectedGroup);
    }
  }, [selectedGroup]);

  const loadGroups = async () => {
    try {
      setLoading(true);
      const groupsData = await apiService.getAllGroups();
      setGroups(groupsData);
      
      if (groupsData.length > 0) {
        setSelectedGroup(groupsData[0].id);
      }
    } catch (error) {
      console.error("Error loading groups:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadSettlements = async (groupId: number) => {
    try {
      setLoadingSettlements(true);
      const settlementsData = await apiService.getGroupSettlements(groupId);
      setSettlements(settlementsData.settlements || []);
    } catch (error) {
      console.error("Error loading settlements:", error);
      setSettlements([]);
    } finally {
      setLoadingSettlements(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500 mx-auto"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center space-x-2 mb-6">
        <ArrowRightLeft className="h-6 w-6 text-blue-500" />
        <h1 className="text-2xl font-bold text-gray-900">Settlement Suggestions</h1>
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
          {groups.map((group) => (
            <option key={group.id} value={group.id}>
              {group.name} (${group.total_expenses.toFixed(2)})
            </option>
          ))}
        </select>
      </div>

      {selectedGroup && (
        <div className="bg-white shadow rounded-lg">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">
              Recommended Settlements
            </h3>
            <p className="text-sm text-gray-500 mt-1">
              Minimize transactions by following these settlement suggestions
            </p>
          </div>

          {loadingSettlements ? (
            <div className="p-6 text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
              <p className="text-sm text-gray-500 mt-2">Loading settlements...</p>
            </div>
          ) : settlements.length > 0 ? (
            <div className="divide-y divide-gray-200">
              {settlements.map((settlement, index) => (
                <div key={index} className="px-6 py-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <div className="flex-shrink-0">
                        <div className="h-10 w-10 rounded-full bg-red-100 flex items-center justify-center">
                          <span className="text-red-600 font-medium text-sm">
                            {settlement.from_user.charAt(0).toUpperCase()}
                          </span>
                        </div>
                      </div>
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {settlement.from_user}
                        </div>
                        <div className="text-xs text-gray-500">
                          Owes money
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-4">
                      <div className="text-center">
                        <ArrowRightLeft className="h-5 w-5 text-gray-400 mx-auto" />
                        <div className="text-lg font-bold text-green-600">
                          ${settlement.amount.toFixed(2)}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-4">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {settlement.to_user}
                        </div>
                        <div className="text-xs text-gray-500">
                          Should receive
                        </div>
                      </div>
                      <div className="flex-shrink-0">
                        <div className="h-10 w-10 rounded-full bg-green-100 flex items-center justify-center">
                          <span className="text-green-600 font-medium text-sm">
                            {settlement.to_user.charAt(0).toUpperCase()}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-3 text-xs text-gray-500 text-center">
                    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                      {settlement.from_user} → {settlement.to_user}: ${settlement.amount.toFixed(2)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-6 text-center">
              <DollarSign className="mx-auto h-12 w-12 text-gray-400" />
              <h3 className="mt-2 text-sm font-medium text-gray-900">
                All settled up!
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                No settlements needed for this group. Everyone is even.
              </p>
            </div>
          )}

          {settlements.length > 0 && (
            <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
              <div className="text-sm text-gray-600">
                <p className="font-medium">How to settle:</p>
                <ol className="list-decimal list-inside mt-2 space-y-1">
                  {settlements.map((settlement, index) => (
                    <li key={index}>
                      <span className="font-medium">{settlement.from_user}</span> pays{" "}
                      <span className="font-medium">${settlement.amount.toFixed(2)}</span> to{" "}
                      <span className="font-medium">{settlement.to_user}</span>
                    </li>
                  ))}
                </ol>
              </div>
            </div>
          )}
        </div>
      )}

      {!selectedGroup && groups.length === 0 && (
        <div className="text-center py-8">
          <ArrowRightLeft className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No groups available</h3>
          <p className="mt-1 text-sm text-gray-500">
            Create a group and add expenses first to see settlement suggestions.
          </p>
        </div>
      )}
    </div>
  );
};

export default Settlements;
