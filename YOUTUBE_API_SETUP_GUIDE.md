# YouTube Data API v3 Setup Guide for TestAlex

## 🎯 Current Status
- ✅ googleapis npm package installed
- ✅ YouTube API utility class created (`youtube-api-setup.js`)
- ✅ Environment variables configured (using existing `GOOGLE_CLOUD_API_KEY`)
- ❌ **YouTube Data API v3 needs to be enabled in Google Cloud Console**

## 🚀 Step-by-Step Setup

### Step 1: Enable YouTube Data API v3

**Quick Link**: [Enable YouTube Data API v3](https://console.developers.google.com/apis/api/youtube.googleapis.com/overview?project=1002911619347)

**Manual Steps**:

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Make sure you're in the correct project: `acim-guide-production` (Project ID: 1002911619347)

2. **Navigate to APIs & Services**
   - Click on "APIs & Services" in the left sidebar
   - Click on "Library"

3. **Search for YouTube Data API**
   - In the search box, type: "YouTube Data API v3"
   - Click on "YouTube Data API v3"

4. **Enable the API**
   - Click the "Enable" button
   - Wait for the API to be enabled (usually takes a few seconds)

5. **Verify API Key Access** (Optional but recommended)
   - Go to "APIs & Services" > "Credentials"
   - Find your existing API key (currently used for Firebase)
   - Click "Edit" and ensure YouTube Data API v3 is not restricted

### Step 2: Test the Installation

Once the API is enabled, run the test script:

```bash
node youtube-api-setup.js
```

You should see output like:
```
✅ YouTube Data API v3 initialized successfully
🧪 Testing YouTube Data API v3...
1️⃣ Validating API...
{ success: true, message: 'YouTube Data API v3 is working correctly' }
2️⃣ Searching for ACIM spiritual content...
Found 5 ACIM videos:
  1. A Course in Miracles - Forgiveness (Channel Name)
  2. ...
```

### Step 3: Integration Options

#### Option A: Basic Search Integration

```javascript
// In your Firebase Functions or frontend
const YouTubeAPIManager = require('./youtube-api-setup');

const ytAPI = new YouTubeAPIManager();

// Search for spiritual content
const results = await ytAPI.searchACIMContent('forgiveness', 10);
console.log(results.videos);
```

#### Option B: Advanced Firebase Function Integration

```javascript
// functions/index.js - Add YouTube API endpoint
const YouTubeAPIManager = require('./youtube-api-setup');

exports.searchSpiritualVideos = functions.https.onCall(async (data, context) => {
    try {
        const { query, maxResults = 10 } = data;
        const ytAPI = new YouTubeAPIManager();
        
        // Search for ACIM-related content
        const results = await ytAPI.searchACIMContent(query, maxResults);
        
        return {
            success: true,
            videos: results.videos,
            message: `Found ${results.videos.length} spiritual videos`
        };
    } catch (error) {
        console.error('YouTube search error:', error);
        return {
            success: false,
            error: error.message
        };
    }
});
```

#### Option C: React Component Integration

```jsx
// components/SpiritualVideoSearch.jsx
import { useState } from 'react';
import { httpsCallable } from 'firebase/functions';

const SpiritualVideoSearch = () => {
    const [videos, setVideos] = useState([]);
    const [loading, setLoading] = useState(false);
    
    const searchVideos = httpsCallable(functions, 'searchSpiritualVideos');
    
    const handleSearch = async (query) => {
        setLoading(true);
        try {
            const result = await searchVideos({ query, maxResults: 5 });
            setVideos(result.data.videos);
        } catch (error) {
            console.error('Video search failed:', error);
        }
        setLoading(false);
    };
    
    return (
        <div className="spiritual-video-search">
            <h3>Find ACIM Spiritual Videos</h3>
            {/* Search interface here */}
        </div>
    );
};
```

## 📊 API Quotas and Limits

### YouTube Data API v3 Quotas
- **Default Quota**: 10,000 units per day
- **Search Operation**: 100 units per request
- **Video Details**: 1 unit per video
- **Channel Info**: 1 unit per channel

### Cost Estimation
- **100 searches/day**: 10,000 units (uses full quota)
- **10 searches + video details**: ~1,100 units
- **Typical usage for ACIMguide**: ~1,000-3,000 units/day

### Rate Limiting Recommendations
```javascript
// Add to your implementation
const RATE_LIMIT = {
    searchesPerHour: 50,
    searchesPerUser: 10,
    cooldownMinutes: 5
};
```

## 🔒 Security Best Practices

### API Key Restrictions (Recommended)
1. **Go to Google Cloud Console > Credentials**
2. **Edit your API key**
3. **Add Application Restrictions**:
   - HTTP referrers: `acim-guide-production.web.app/*`
   - Firebase domain: `acim-guide-production.firebaseapp.com/*`
4. **Add API Restrictions**:
   - Only enable: "YouTube Data API v3"

### Environment Security
- ✅ API key is already in `.env` (not committed to Git)
- ✅ Firebase Functions environment automatically secured
- 📝 Consider separate API key for development vs production

## 🎯 TestAlex Integration Ideas

### 1. Spiritual Video Library
- Curate ACIM teachers and channels
- Create playlists for specific spiritual topics
- Video recommendations based on user interests

### 2. Course Enhancement
- Add video examples to €7 courses
- Supplement CourseGPT responses with relevant videos
- Create multimedia spiritual lessons

### 3. Community Features
- Share meaningful spiritual videos
- Comment on videos from spiritual perspective
- Build video-based discussion groups

### 4. Premium Features
- Advanced video search and filtering
- Personal video collections
- Offline video recommendations

## 🛠️ Available Methods

### Core Functions
```javascript
const ytAPI = new YouTubeAPIManager();

// Search for videos
await ytAPI.searchVideos("A Course in Miracles", 25);

// Get video details
await ytAPI.getVideoDetails("VIDEO_ID");

// Get channel information
await ytAPI.getChannelInfo("CHANNEL_ID");

// Search ACIM-specific content
await ytAPI.searchACIMContent("forgiveness", 10);

// Get video comments
await ytAPI.getVideoComments("VIDEO_ID", 20);

// Validate API
await ytAPI.validateAPI();
```

## 🔧 Troubleshooting

### Common Issues

1. **"API not enabled" Error**
   - Solution: Follow Step 1 above to enable the API

2. **"Quota exceeded" Error**
   - Check current usage in Cloud Console
   - Implement rate limiting
   - Consider requesting quota increase

3. **"Access denied" Error**
   - Check API key restrictions
   - Verify domain whitelist includes your Firebase domain

4. **"Video unavailable" Error**
   - Some videos are region-restricted
   - Private videos won't be accessible
   - Age-restricted content requires special handling

### Debug Mode
```bash
# Enable debug logging
NODE_ENV=development node youtube-api-setup.js
```

## 📈 Next Steps After Setup

1. **Enable the API** (Step 1 above)
2. **Test the installation** (Step 2 above)
3. **Choose integration option** (Step 3 above)
4. **Implement rate limiting** for production
5. **Add spiritual content curation**
6. **Integrate with ACIMguide UI**

---

## 📞 Support

If you encounter issues:
1. Check the [YouTube API documentation](https://developers.google.com/youtube/v3)
2. Verify your Google Cloud Console settings
3. Test with the provided validation script
4. Review quota usage in Cloud Console

**Remember**: This integration should align with TestAlex's spiritual mission - focus on authentic ACIM content and spiritual growth rather than entertainment or worldly content.
