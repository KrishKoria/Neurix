import React, { useState, useEffect } from "react";
import { apiService, type Group } from "../lib/api";
import { BarChart3, TrendingUp, Users, DollarSign } from "lucide-react";

interface ExpenseStats {
  total_expenses: number;
  total_amount: number;
  average_amount: number;
  minimum_amount: number;
  maximum_amount: number;
}

const ExpenseStatistics = () => {
  const [stats, setStats] = useState<ExpenseStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStatistics();
  }, []);

  const loadStatistics = async () => {
    try {
      setLoading(true);
      const statsData = await apiService.getExpenseStatistics();
      setStats(statsData);
    } catch (error) {
      console.error("Error loading statistics:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-500 mx-auto"></div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="p-6">
        <div className="text-center py-8">
          <BarChart3 className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">
            No statistics available
          </h3>
          <p className="mt-1 text-sm text-gray-500">
            Add some expenses to see statistics.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex items-center space-x-2 mb-6">
        <BarChart3 className="h-6 w-6 text-blue-500" />
        <h1 className="text-2xl font-bold text-gray-900">Expense Statistics</h1>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <BarChart3 className="h-8 w-8 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Total Expenses
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {stats.total_expenses}
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
                <DollarSign className="h-8 w-8 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Total Amount
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    ${stats.total_amount.toFixed(2)}
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
                <TrendingUp className="h-8 w-8 text-gray-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Average Expense
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    ${stats.average_amount.toFixed(2)}
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
                <DollarSign className="h-8 w-8 text-red-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Highest Expense
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    ${stats.maximum_amount.toFixed(2)}
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
                <DollarSign className="h-8 w-8 text-green-400" />
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Lowest Expense
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    ${stats.minimum_amount.toFixed(2)}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Summary Card */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">
            Expense Summary
          </h3>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <div className="text-sm font-medium text-gray-700 mb-2">
                Total Amount Spent
              </div>
              <div className="text-3xl font-bold text-blue-600">
                ${stats.total_amount.toFixed(2)}
              </div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-700 mb-2">
                Number of Expenses
              </div>
              <div className="text-3xl font-bold text-gray-900">
                {stats.total_expenses}
              </div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-700 mb-2">
                Average per Expense
              </div>
              <div className="text-2xl font-semibold text-green-600">
                ${stats.average_amount.toFixed(2)}
              </div>
            </div>
            <div>
              <div className="text-sm font-medium text-gray-700 mb-2">
                Expense Range
              </div>
              <div className="text-lg text-gray-900">
                ${stats.minimum_amount.toFixed(2)} - ${stats.maximum_amount.toFixed(2)}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExpenseStatistics;
