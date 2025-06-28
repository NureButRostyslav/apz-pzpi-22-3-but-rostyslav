package com.coworking_system

import android.app.PendingIntent
import android.content.Intent
import android.nfc.NfcAdapter
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.coworking_system.api.ApiService
import com.coworking_system.models.*
import com.google.firebase.messaging.FirebaseMessaging
import kotlinx.coroutines.launch
import java.time.LocalDateTime
import java.time.format.DateTimeFormatter
import java.util.*

class MainActivity : ComponentActivity() {
    private lateinit var nfcAdapter: NfcAdapter

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        nfcAdapter = NfcAdapter.getDefaultAdapter(this)
        if (nfcAdapter == null) {
            Toast.makeText(this, getString(R.string.nfc_not_supported), Toast.LENGTH_LONG).show()
        }
        setContent {
            CoworkingApp()
        }
        FirebaseMessaging.getInstance().subscribeToTopic("budget_notifications")
        FirebaseMessaging.getInstance().subscribeToTopic("expense_updates")
        FirebaseMessaging.getInstance().subscribeToTopic("analytics_updates")
    }

    override fun onResume() {
        super.onResume()
        if (nfcAdapter != null) {
            val intent = Intent(this, javaClass).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP)
            val pendingIntent = PendingIntent.getActivity(this, 0, intent, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_MUTABLE)
            nfcAdapter.enableForegroundDispatch(this, pendingIntent, null, null)
        }
    }

    override fun onPause() {
        super.onPause()
        nfcAdapter?.disableForegroundDispatch(this)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        if (NfcAdapter.ACTION_TAG_DISCOVERED == intent.action) {
            val tagId = intent.getByteArrayExtra(NfcAdapter.EXTRA_ID)?.joinToString("") { "%02x".format(it) } ?: ""
            Toast.makeText(this, "${getString(R.string.nfc_detected)}: $tagId", Toast.LENGTH_SHORT).show()
            val scope = kotlinx.coroutines.MainScope()
            scope.launch {
                try {
                    ApiService.activateAccess(tagId)
                    Toast.makeText(this@MainActivity, R.string.access_granted, Toast.LENGTH_SHORT).show()
                } catch (e: Exception) {
                    Toast.makeText(this@MainActivity, R.string.access_failed, Toast.LENGTH_SHORT).show()
                }
            }
        }
    }
}

@Composable
fun CoworkingApp() {
    val context = LocalContext.current
    val scope = rememberCoroutineScope()
    var resources by remember { mutableStateOf<List<Resource>>(emptyList()) }
    var selectedResource by remember { mutableStateOf<Resource?>(null) }
    var startTime by remember { mutableStateOf(LocalDateTime.now()) }
    var endTime by remember { mutableStateOf(LocalDateTime.now().plusHours(1)) }
    var expenses by remember { mutableStateOf<List<Expense>>(emptyList()) }
    var bookings by remember { mutableStateOf<List<Booking>>(emptyList()) }
    var limitAmount by remember { mutableStateOf("") }
    var limitCategory by remember { mutableStateOf("") }
    var notificationThreshold by remember { mutableStateOf("") }
    var notificationMethod by remember { mutableStateOf("email") }
    var locale by remember { mutableStateOf(Locale.getDefault().language) }
    var analytics by remember { mutableStateOf<List<Analytics>>(emptyList()) }
    var errorMessage by remember { mutableStateOf("") }

    LaunchedEffect(Unit) {
        try {
            resources = ApiService.getResources()
            expenses = ApiService.getExpenses()
            bookings = ApiService.getBookings()
            analytics = ApiService.getAnalytics()
        } catch (e: Exception) {
            errorMessage = e.message ?: context.getString(R.string.error_fetching_data)
        }
    }

    Column(modifier = Modifier.padding(16.dp)) {
        Text(
            text = stringResource(id = R.string.app_title),
            style = MaterialTheme.typography.headlineMedium,
            fontWeight = FontWeight.Bold
        )
        Spacer(modifier = Modifier.height(16.dp))

        DropdownMenu(
            items = listOf("uk", "en"),
            selectedItem = locale,
            onItemSelected = { lang ->
                locale = lang
                val newLocale = Locale(lang)
                Locale.setDefault(newLocale)
                val config = context.resources.configuration
                config.setLocale(newLocale)
                context.resources.updateConfiguration(config, context.resources.displayMetrics)
            },
            label = stringResource(id = R.string.select_language)
        )

        Spacer(modifier = Modifier.height(16.dp))

        DropdownMenu(
            items = resources.map { it.name },
            selectedItem = selectedResource?.name ?: "",
            onItemSelected = { name ->
                selectedResource = resources.find { it.name == name }
            },
            label = stringResource(id = R.string.select_resource)
        )

        OutlinedTextField(
            value = startTime.format(DateTimeFormatter.ISO_LOCAL_DATE_TIME),
            onValueChange = { startTime = LocalDateTime.parse(it) },
            label = { Text(stringResource(id = R.string.start_time)) },
            modifier = Modifier.fillMaxWidth()
        )
        OutlinedTextField(
            value = endTime.format(DateTimeFormatter.ISO_LOCAL_DATE_TIME),
            onValueChange = { endTime = LocalDateTime.parse(it) },
            label = { Text(stringResource(id = R.string.end_time)) },
            modifier = Modifier.fillMaxWidth()
        )
        Button(
            onClick = {
                scope.launch {
                    selectedResource?.let {
                        val booking = Booking(
                            resourceId = it.id,
                            startTime = startTime,
                            endTime = endTime
                        )
                        try {
                            val response = ApiService.createBooking(booking)
                            if (response.success) {
                                Toast.makeText(context, R.string.booking_success, Toast.LENGTH_SHORT).show()
                                expenses = ApiService.getExpenses()
                                bookings = ApiService.getBookings()
                            } else {
                                Toast.makeText(context, response.message ?: context.getString(R.string.booking_failed), Toast.LENGTH_SHORT).show()
                            }
                        } catch (e: Exception) {
                            Toast.makeText(context, e.message ?: context.getString(R.string.booking_failed), Toast.LENGTH_SHORT).show()
                        }
                    }
                }
            },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text(stringResource(id = R.string.book))
        }

        Spacer(modifier = Modifier.height(16.dp))

        Text(
            text = stringResource(id = R.string.limit_management),
            style = MaterialTheme.typography.headlineSmall,
            fontSize = 20.sp
        )
        OutlinedTextField(
            value = limitAmount,
            onValueChange = { limitAmount = it },
            label = { Text(stringResource(id = R.string.set_limit)) },
            modifier = Modifier.fillMaxWidth()
        )
        OutlinedTextField(
            value = limitCategory,
            onValueChange = { limitCategory = it },
            label = { Text(stringResource(id = R.string.limit_category)) },
            modifier = Modifier.fillMaxWidth()
        )
        Button(
            onClick = {
                scope.launch {
                    try {
                        val limit = Limit(
                            userId = ApiService.getCurrentUserId(),
                            amount = limitAmount.toDoubleOrNull() ?: 0.0,
                            category = limitCategory.takeIf { it.isNotBlank() }
                        )
                        ApiService.setLimit(limit)
                        Toast.makeText(context, R.string.limit_set_success, Toast.LENGTH_SHORT).show()
                        limitAmount = ""
                        limitCategory = ""
                    } catch (e: Exception) {
                        Toast.makeText(context, e.message ?: context.getString(R.string.limit_set_failed), Toast.LENGTH_SHORT).show()
                    }
                }
            },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text(stringResource(id = R.string.save_limit))
        }

        Spacer(modifier = Modifier.height(16.dp))

        Text(
            text = stringResource(id = R.string.notification_settings),
            style = MaterialTheme.typography.headlineSmall,
            fontSize = 20.sp
        )
        OutlinedTextField(
            value = notificationThreshold,
            onValueChange = { notificationThreshold = it },
            label = { Text(stringResource(id = R.string.notification_threshold)) },
            modifier = Modifier.fillMaxWidth()
        )
        DropdownMenu(
            items = listOf("email", "push"),
            selectedItem = notificationMethod,
            onItemSelected = { notificationMethod = it },
            label = stringResource(id = R.string.notification_method)
        )
        Button(
            onClick = {
                scope.launch {
                    try {
                        ApiService.setNotificationThreshold(NotificationSettings(notificationThreshold.toDoubleOrNull() ?: 0.0, notificationMethod))
                        Toast.makeText(context, R.string.notification_set_success, Toast.LENGTH_SHORT).show()
                        notificationThreshold = ""
                    } catch (e: Exception) {
                        Toast.makeText(context, e.message ?: context.getString(R.string.notification_set_failed), Toast.LENGTH_SHORT).show()
                    }
                }
            },
            modifier = Modifier.fillMaxWidth()
        ) {
            Text(stringResource(id = R.string.save_notification))
        }

        Spacer(modifier = Modifier.height(16.dp))

        Text(
            text = stringResource(id = R.string.recent_bookings),
            style = MaterialTheme.typography.headlineSmall,
            fontSize = 20.sp
        )
        LazyColumn {
            items(bookings) { booking ->
                Card(modifier = Modifier.padding(8.dp)) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text("${stringResource(id = R.string.resource)}: ${booking.resourceName}")
                        Text("${stringResource(id = R.string.start_time)}: ${booking.startTime.format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)}")
                        Text("${stringResource(id = R.string.end_time)}: ${booking.endTime.format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)}")
                        Button(
                            onClick = {
                                scope.launch {
                                    try {
                                        ApiService.cancelBooking(booking.id)
                                        Toast.makeText(context, R.string.booking_cancel_success, Toast.LENGTH_SHORT).show()
                                        bookings = ApiService.getBookings()
                                        expenses = ApiService.getExpenses()
                                    } catch (e: Exception) {
                                        Toast.makeText(context, e.message ?: context.getString(R.string.booking_cancel_failed), Toast.LENGTH_SHORT).show()
                                    }
                                }
                            }
                        ) {
                            Text(stringResource(id = R.string.cancel_booking))
                        }
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        Text(
            text = stringResource(id = R.string.recent_expenses),
            style = MaterialTheme.typography.headlineSmall,
            fontSize = 20.sp
        )
        LazyColumn {
            items(expenses) { expense ->
                Card(modifier = Modifier.padding(8.dp)) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text("${stringResource(id = R.string.resource)}: ${expense.resource}")
                        Text("${stringResource(id = R.string.cost)}: ${expense.totalCost}")
                        Text("${stringResource(id = R.string.start_time)}: ${expense.startTime.format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)}")
                    }
                }
            }
        }

        Spacer(modifier = Modifier.height(16.dp))

        Text(
            text = stringResource(id = R.string.analytics),
            style = MaterialTheme.typography.headlineSmall,
            fontSize = 20.sp
        )
        LazyColumn {
            items(analytics) { analytic ->
                Card(modifier = Modifier.padding(8.dp)) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text("${stringResource(id = R.string.resource)}: ${analytic.resource}")
                        Text("${stringResource(id = R.string.total_cost)}: ${analytic.totalCost}")
                        Text("${stringResource(id = R.string.usage_hours)}: ${analytic.usageHours}")
                    }
                }
            }
        }

        if (errorMessage.isNotEmpty()) {
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = errorMessage,
                color = MaterialTheme.colors.error,
                modifier = Modifier.align(Alignment.CenterHorizontally)
            )
        }
    }
}

@Composable
fun DropdownMenu(
    items: List<String>,
    selectedItem: String,
    onItemSelected: (String) -> Unit,
    label: String
) {
    var expanded by remember { mutableStateOf(false) }

    Box {
        OutlinedTextField(
            value = selectedItem,
            onValueChange = {},
            label = { Text(label) },
            modifier = Modifier.fillMaxWidth(),
            readOnly = true
        )
        DropdownMenu(
            expanded = expanded,
            onDismissRequest = { expanded = false }
        ) {
            items.forEach { item ->
                DropdownMenuItem(
                    text = { Text(item) },
                    onClick = {
                        onItemSelected(item)
                        expanded = false
                    }
                )
            }
        }
        Spacer(modifier = Modifier.matchParentSize().clickable { expanded = true })
    }
}
