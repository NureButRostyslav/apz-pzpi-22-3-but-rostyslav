package com.coworking_system

import android.content.Context
import com.coworking_system.models.Booking
import com.coworking_system.models.Expense
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import java.io.File
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter

object BackupManager {
    fun backupUserData(context: Context, userId: Int, expenses: List<Expense>, bookings: List<Booking>): String {
        val timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss"))
        val backupDir = File(context.filesDir, "backups")
        backupDir.mkdirs()
        val filename = "user_${userId}_backup_$timestamp.json"
        val file = File(backupDir, filename)
        val backupData = mapOf(
            "expenses" to expenses.map { mapOf(
                "resource" to it.resource,
                "total_cost" to it.totalCost,
                "start_time" to it.startTime.toString()
            ) },
            "bookings" to bookings.map { mapOf(
                "resource_name" to it.resourceName,
                "start_time" to it.startTime.toString(),
                "end_time" to it.endTime.toString()
            ) }
        )
        file.writeText(Json.encodeToString(backupData))
        return file.absolutePath
    }

    fun restoreUserData(context: Context, filename: String): Pair<List<Expense>, List<Booking>> {
        val file = File(filename)
        val json = file.readText()
        val backupData = Json.decodeFromString<Map<String, List<Map<String, String>>>>(json)
        val expenses = backupData["expenses"]?.map {
            Expense(
                resource = it["resource"] ?: "",
                totalCost = it["total_cost"]?.toDouble() ?: 0.0,
                startTime = LocalDateTime.parse(it["start_time"])
            )
        } ?: emptyList()
        val bookings = backupData["bookings"]?.map {
            Booking(
                id = 0,
                resourceId = 0,
                resourceName = it["resource_name"] ?: "",
                startTime = LocalDateTime.parse(it["start_time"]),
                endTime = LocalDateTime.parse(it["end_time"])
            )
        } ?: emptyList()
        return Pair(expenses, bookings)
    }
}
