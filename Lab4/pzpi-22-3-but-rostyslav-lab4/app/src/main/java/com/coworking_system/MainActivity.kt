package com.coworking_system

import android.app.PendingIntent
import android.content.Intent
import android.nfc.NfcAdapter
import android.os.Bundle
import android.widget.Toast
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import com.coworking_system.api.ApiService
import com.coworking_system.models.Booking
import com.coworking_system.models.Expense
import com.coworking_system.models.Limit
import com.coworking_system.models.Resource
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

        // Subscribe to push notifications
        FirebaseMessaging.getInstance().subscribeToTopic("budget_notifications")
        FirebaseMessaging.getInstance().subscribeToTopic("expense_updates")
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
            // Send NFC data to server
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
    var limitAmount by remember { mutableStateOf("") }
    var notificationThreshold by remember { mutableStateOf("") }
    var locale by remember { mutableStateOf(Locale.getDefault().language) }

    LaunchedEffect(Unit) {
        resources = ApiService.getResources()
        expenses = ApiService.getExpenses()
    }

    Column(modifier = Modifier.padding(16.dp)) {
        Text(
            text = stringResource(id = R.string.app_title),
            style = MaterialTheme.typography.headlineMedium
        )
        Spacer(modifier = Modifier.height(16.dp))

        // Language selection
        DropdownMenu(
            items = listOf("uk", "en"),
            onItemSelected = { lang ->
                locale = lang
                // Update locale
                val newLocale = Locale(lang)
                Locale.setDefault(newLocale)
                val config = context.resources.configuration
                config.setLocale(newLocale)
                context.resources.updateConfiguration(config, context.resources.displayMetrics)
            },
            label = stringResource(id = R.string.select_language)
        )

        // Resource selection
        DropdownMenu(
            items = resources.map { it.name },
            onItemSelected = { name ->
                selectedResource = resources.find { it.name == name }
            },
            label = stringResource(id = R.string.select_resource)
        )

        // Booking form
        OutlinedTextField(
            value = startTime.format(DateTimeFormatter.ISO_LOCAL_DATE_TIME),
            onValueChange = { startTime = LocalDateTime.parse(it) },
            label = { Text(stringResource(id = R.string.start_time)) }
        )
        OutlinedTextField(
            value = endTime.format(DateTimeFormatter.ISO_LOCAL_DATE_TIME),
            onValueChange = { endTime = LocalDateTime.parse(it) },
            label = { Text(stringResource(id = R.string.end_time)) }
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
                        val response = ApiService.createBooking(booking)
                        if (response.success) {
                            Toast.makeText(context, R.string.booking_success, Toast.LENGTH_SHORT).show()
                            expenses = ApiService.getExpenses()
                        } else {
                            Toast.makeText(context, R.string.booking_failed, Toast.LENGTH_SHORT).show()
                        }
                    }
                }
            }
        ) {
            Text(stringResource(id = R.string.book))
        }

        // Limit management
        OutlinedTextField(
            value = limitAmount,
            onValueChange = { limitAmount = it },
            label = { Text(stringResource(id = R.string.set_limit)) }
        )
        Button(
            onClick = {
                scope.launch {
                    val limit = Limit(
                        userId = ApiService.getCurrentUserId(),
                        amount = limitAmount.toDoubleOrNull() ?: 0.0
                    )
                    ApiService.setLimit(limit)
                    Toast.makeText(context, R.string.limit_set_success, Toast.LENGTH_SHORT).show()
                }
            }
        ) {
            Text(stringResource(id = R.string.save_limit))
        }

        // Notification settings
        OutlinedTextField(
            value = notificationThreshold,
            onValueChange = { notificationThreshold = it },
            label = { Text(stringResource(id = R.string.notification_threshold)) }
        )
        Button(
            onClick = {
                scope.launch {
                    ApiService.setNotificationThreshold(notificationThreshold.toDoubleOrNull() ?: 0.0)
                    Toast.makeText(context, R.string.notification_set_success, Toast.LENGTH_SHORT).show()
                }
            }
        ) {
            Text(stringResource(id = R.string.save_notification))
        }

        // Real-time expenses
        Text(stringResource(id = R.string.recent_expenses))
        expenses.forEach { expense ->
            Card(modifier = Modifier.padding(8.dp)) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("${stringResource(id = R.string.resource)}: ${expense.resource}")
                    Text("${stringResource(id = R.string.cost)}: ${expense.totalCost}")
                    Text("${stringResource(id = R.string.start_time)}: ${expense.startTime}")
                }
            }
        }
    }
}

@Composable
fun DropdownMenu(
    items: List<String>,
    onItemSelected: (String) -> Unit,
    label: String
) {
    var expanded by remember { mutableStateOf(false) }
    var selectedItem by remember { mutableStateOf("") }

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
                        selectedItem = item
                        onItemSelected(item)
                        expanded = false
                    }
                )
            }
        }
        Spacer(modifier = Modifier.matchParentSize().clickable { expanded = true })
    }
}
