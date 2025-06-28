package com.coworking_system.api

import com.coworking_system.models.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.*
import java.time.LocalDateTime
import java.util.*

interface ApiInterface {
    @GET("resources/")
    suspend fun getResources(): List<Resource>

    @POST("expenses/")
    suspend fun createBooking(@Body booking: Booking): BookingResponse

    @GET("expenses/")
    suspend fun getExpenses(): List<Expense>

    @GET("bookings/")
    suspend fun getBookings(): List<Booking>

    @DELETE("bookings/{id}/")
    suspend fun cancelBooking(@Path("id") id: Int): Response<Unit>

    @POST("limits/")
    suspend fun setLimit(@Body limit: Limit): Response<Unit>

    @POST("access/")
    suspend fun activateAccess(@Body request: AccessRequest): Response<Unit>

    @POST("notifications/")
    suspend fun setNotificationThreshold(@Body settings: NotificationSettings): Response<Unit>

    @GET("analytics/")
    suspend fun getAnalytics(): List<Analytics>
}

data class Resource(val id: Int, val name: String, val costPerHour: Double)
data class Booking(val id: Int = 0, val resourceId: Int, val resourceName: String = "", val startTime: LocalDateTime, val endTime: LocalDateTime)
data class Expense(val resource: String, val totalCost: Double, val startTime: LocalDateTime)
data class Limit(val userId: Int, val amount: Double, val category: String? = null)
data class AccessRequest(val tagId: String)
data class NotificationSettings(val threshold: Double, val method: String)
data class Analytics(val resource: String, val totalCost: Double, val usageHours: Double)
data class BookingResponse(val success: Boolean, val message: String? = null)
data class Response<T>(val data: T)

object ApiService {
    private val retrofit = Retrofit.Builder()
        .baseUrl("http://your-server-ip:8000/api/")
        .addConverterFactory(GsonConverterFactory.create())
        .client(OkHttpClient.Builder().addInterceptor { chain ->
            chain.proceed(
                chain.request().newBuilder()
                    .addHeader("Authorization", "Bearer ${getToken()}")
                    .addHeader("Accept-Language", Locale.getDefault().language)
                    .build()
            )
        }.build())
        .build()

    private val api = retrofit.create(ApiInterface::class.java)

    private fun getToken(): String {
        return "your-jwt-token"
    }

    fun getCurrentUserId(): Int {
        return 1
    }

    suspend fun getResources(): List<Resource> = withContext(Dispatchers.IO) {
        api.getResources()
    }

    suspend fun createBooking(booking: Booking): BookingResponse = withContext(Dispatchers.IO) {
        try {
            api.createBooking(booking)
        } catch (e: Exception) {
            BookingResponse(success = false, message = e.message)
        }
    }

    suspend fun getExpenses(): List<Expense> = withContext(Dispatchers.IO) {
        api.getExpenses()
    }

    suspend fun getBookings(): List<Booking> = withContext(Dispatchers.IO) {
        api.getBookings()
    }

    suspend fun cancelBooking(id: Int) = withContext(Dispatchers.IO) {
        api.cancelBooking(id)
    }

    suspend fun setLimit(limit: Limit) = withContext(Dispatchers.IO) {
        api.setLimit(limit)
    }

    suspend fun activateAccess(tagId: String) = withContext(Dispatchers.IO) {
        api.activateAccess(AccessRequest(tagId))
    }

    suspend fun setNotificationThreshold(settings: NotificationSettings) = withContext(Dispatchers.IO) {
        api.setNotificationThreshold(settings)
    }

    suspend fun getAnalytics(): List<Analytics> = withContext(Dispatchers.IO) {
        api.getAnalytics()
    }
}
