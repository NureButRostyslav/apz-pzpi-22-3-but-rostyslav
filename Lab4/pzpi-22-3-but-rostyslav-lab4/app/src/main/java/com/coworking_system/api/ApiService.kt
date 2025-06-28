package com.coworking_system.api

import com.coworking_system.models.Booking
import com.coworking_system.models.Expense
import com.coworking_system.models.Limit
import com.coworking_system.models.Resource
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.http.*
import java.time.LocalDateTime

interface ApiInterface {
    @GET("resources/")
    suspend fun getResources(): List<Resource>

    @POST("expenses/")
    suspend fun createBooking(@Body booking: Booking): BookingResponse

    @GET("expenses/")
    suspend fun getExpenses(): List<Expense>

    @POST("limits/")
    suspend fun setLimit(@Body limit: Limit): Response<Unit>

    @POST("access/")
    suspend fun activateAccess(@Body request: AccessRequest): Response<Unit>

    @POST("notifications/")
    suspend fun setNotificationThreshold(@Body threshold: ThresholdRequest): Response<Unit>
}

data class Resource(val id: Int, val name: String, val costPerHour: Double)
data class Booking(val resourceId: Int, val startTime: LocalDateTime, val endTime: LocalDateTime)
data class Expense(val resource: String, val totalCost: Double, val startTime: LocalDateTime)
data class Limit(val userId: Int, val amount: Double, val category: String? = null)
data class AccessRequest(val tagId: String)
data class ThresholdRequest(val threshold: Double)
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
        // Implement secure token retrieval (e.g., from SharedPreferences)
        return "your-jwt-token"
    }

    fun getCurrentUserId(): Int {
        // Implement user ID retrieval
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

    suspend fun setLimit(limit: Limit) = withContext(Dispatchers.IO) {
        api.setLimit(limit)
    }

    suspend fun activateAccess(tagId: String) = withContext(Dispatchers.IO) {
        api.activateAccess(AccessRequest(tagId))
    }

    suspend fun setNotificationThreshold(threshold: Double) = withContext(Dispatchers.IO) {
        api.setNotificationThreshold(ThresholdRequest(threshold))
    }
}
