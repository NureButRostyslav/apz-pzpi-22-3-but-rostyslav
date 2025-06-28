package com.coworking_system

import com.coworking_system.models.Expense
import java.time.LocalDateTime

object AnalyticsProcessor {
    fun calculateTrends(expenses: List<Expense>, startDate: LocalDateTime, endDate: LocalDateTime): Map<String, Any> {
        val filteredExpenses = expenses.filter { it.startTime in startDate..endDate }
        val totalCost = filteredExpenses.sumOf { it.totalCost }
        val avgCostPerDay = if (filteredExpenses.isNotEmpty()) totalCost / filteredExpenses.size else 0.0
        val resourceUsage = filteredExpenses.groupBy { it.resource }
            .mapValues { it.value.sumOf { expense -> expense.totalCost } }
        val weeklyTrends = mutableListOf<Map<String, Any>>()
        var currentDate = startDate
        while (currentDate <= endDate) {
            val weekEnd = currentDate.plusDays(6)
            val weekExpenses = filteredExpenses.filter { it.startTime in currentDate..weekEnd }
            val weekTotal = weekExpenses.sumOf { it.totalCost }
            weeklyTrends.add(mapOf("week_start" to currentDate, "total_cost" to weekTotal))
            currentDate = currentDate.plusDays(7)
        }
        return mapOf(
            "total_cost" to totalCost,
            "avg_cost_per_day" to avgCostPerDay,
            "resource_usage" to resourceUsage,
            "weekly_trends" to weeklyTrends
        )
    }

    fun predictExpenses(expenses: List<Expense>, startDate: LocalDateTime, endDate: LocalDateTime): Map<String, Double> {
        val pastExpenses = expenses.filter { it.startTime < startDate }
        val avgDailyCost = if (pastExpenses.isNotEmpty()) pastExpenses.sumOf { it.totalCost } / pastExpenses.size else 0.0
        val days = (endDate.toEpochDay() - startDate.toEpochDay()).toInt()
        val predictedCost = avgDailyCost * days
        return mapOf("predicted_cost" to predictedCost)
    }
}
