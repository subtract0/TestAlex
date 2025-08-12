# ACIMguide Android App

## Quick Start Guide

### 1. Create New Android Project
```
- Open Android Studio
- Create New Project
- Choose "Empty Compose Activity"
- Package name: com.acimguide.mvp
- Language: Kotlin
- Minimum SDK: API 24 (Android 7.0)
```

### 2. Add Dependencies

Add to `app/build.gradle`:

```kotlin
dependencies {
    // Firebase
    implementation 'com.google.firebase:firebase-bom:32.7.0'
    implementation 'com.google.firebase:firebase-auth'
    implementation 'com.google.firebase:firebase-functions'
    implementation 'com.google.firebase:firebase-firestore'
    implementation 'com.google.firebase:firebase-analytics'
    
    // Compose
    implementation 'androidx.compose.ui:ui:1.5.8'
    implementation 'androidx.compose.ui:ui-tooling-preview:1.5.8'
    implementation 'androidx.compose.material3:material3:1.1.2'
    implementation 'androidx.activity:activity-compose:1.8.2'
    implementation 'androidx.lifecycle:lifecycle-viewmodel-compose:2.7.0'
    implementation 'androidx.navigation:navigation-compose:2.7.6'
    
    // Coroutines
    implementation 'org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3'
    
    // JSON
    implementation 'org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.2'
}
```

### 3. Firebase Configuration

Add `google-services.json` to `app/` directory from Firebase Console:
- Go to Project Settings > General
- Download `google-services.json`
- Place in `app/` folder

### 4. Key Features to Implement

#### Authentication
- Google Sign-In integration
- Anonymous authentication fallback
- User session management

#### Chat Interface
- Real-time messaging with Firestore
- Message history persistence
- Typing indicators
- Message status (sent, delivered, read)

#### Quick Actions
- Pre-built ACIM prompts
- Forgiveness walkthrough
- Daily lesson reminders
- Spiritual practice tools

#### Settings
- Tone preference (gentle/direct)
- Notification settings
- Usage statistics
- Data management

### 5. Architecture

```
app/
├── src/main/java/com/acimguide/mvp/
│   ├── ui/
│   │   ├── chat/
│   │   │   ├── ChatScreen.kt
│   │   │   ├── ChatViewModel.kt
│   │   │   └── MessageItem.kt
│   │   ├── auth/
│   │   │   ├── AuthScreen.kt
│   │   │   └── AuthViewModel.kt
│   │   ├── settings/
│   │   │   ├── SettingsScreen.kt
│   │   │   └── SettingsViewModel.kt
│   │   └── theme/
│   │       ├── Color.kt
│   │       ├── Theme.kt
│   │       └── Type.kt
│   ├── data/
│   │   ├── repository/
│   │   │   ├── ChatRepository.kt
│   │   │   └── AuthRepository.kt
│   │   ├── model/
│   │   │   ├── Message.kt
│   │   │   └── User.kt
│   │   └── remote/
│   │       └── FirebaseService.kt
│   ├── di/
│   │   └── AppModule.kt
│   └── MainActivity.kt
```

### 6. Core Components

#### Message Model
```kotlin
data class Message(
    val id: String = "",
    val content: String = "",
    val isUser: Boolean = false,
    val timestamp: Long = System.currentTimeMillis(),
    val status: MessageStatus = MessageStatus.SENDING,
    val citations: List<Citation> = emptyList()
)

enum class MessageStatus {
    SENDING, SENT, DELIVERED, FAILED
}

data class Citation(
    val text: String,
    val source: String,
    val page: Int? = null
)
```

#### Firebase Service
```kotlin
class FirebaseService {
    private val functions = Firebase.functions
    private val firestore = Firebase.firestore
    private val auth = Firebase.auth
    
    suspend fun sendMessage(message: String, tone: String = "gentle"): Result<String> {
        return try {
            val data = hashMapOf(
                "message" to message,
                "tone" to tone
            )
            
            val result = functions
                .getHttpsCallable("chatWithAssistant")
                .call(data)
                .await()
            
            val messageId = result.data as? Map<String, Any>
            Result.success(messageId?.get("messageId") as? String ?: "")
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    fun listenToMessages(userId: String, onMessage: (Message) -> Unit) {
        firestore.collection("messages")
            .whereEqualTo("userId", userId)
            .orderBy("createdAt", Query.Direction.ASCENDING)
            .addSnapshotListener { snapshot, error ->
                if (error != null) return@addSnapshotListener
                
                snapshot?.documents?.forEach { doc ->
                    val message = doc.toObject<Message>()
                    message?.let { onMessage(it) }
                }
            }
    }
}
```

### 7. UI Components

#### Chat Screen
```kotlin
@Composable
fun ChatScreen(
    viewModel: ChatViewModel = hiltViewModel()
) {
    val messages by viewModel.messages.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()
    
    Column(
        modifier = Modifier.fillMaxSize()
    ) {
        LazyColumn(
            modifier = Modifier.weight(1f),
            reverseLayout = true
        ) {
            items(messages.reversed()) { message ->
                MessageItem(message = message)
            }
        }
        
        QuickActionsRow(
            onQuickAction = viewModel::sendQuickAction
        )
        
        MessageInput(
            onSendMessage = viewModel::sendMessage,
            isLoading = isLoading
        )
    }
}
```

### 8. Deployment

#### Build Release APK
```bash
./gradlew assembleRelease
```

#### Play Store Preparation
- App signing key
- Store listing assets
- Privacy policy
- Content rating
- Pricing & distribution

### 9. Testing Strategy

#### Unit Tests
- ViewModel logic
- Repository functions
- Data transformations

#### Integration Tests
- Firebase integration
- API calls
- Database operations

#### UI Tests
- Chat flow
- Authentication
- Settings management

### 10. Performance Optimization

#### Memory Management
- Image caching
- Message pagination
- Background processing

#### Network Optimization
- Request batching
- Offline support
- Retry mechanisms

#### Battery Optimization
- Background sync limits
- Notification efficiency
- Wake lock management

---

## Next Steps

1. **Set up Android Studio project** with above configuration
2. **Implement authentication** with Firebase Auth
3. **Build chat interface** with Compose
4. **Integrate with backend API** (already deployed)
5. **Add quick actions** for ACIM-specific features
6. **Test on device** and iterate
7. **Prepare for Play Store** submission

Your backend is ready and waiting for this mobile app integration!
