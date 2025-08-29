/**
 * YouTube Data API v3 Setup and Utilities for TestAlex
 * 
 * This module provides YouTube API integration for the ACIMguide spiritual platform.
 * It respects the spiritual integrity requirements while providing technical functionality.
 */

const { google } = require('googleapis');
require('dotenv').config();

class YouTubeAPIManager {
    constructor() {
        // Use existing Google Cloud API key from environment
        this.apiKey = process.env.GOOGLE_CLOUD_API_KEY;
        
        if (!this.apiKey) {
            throw new Error('YouTube API requires GOOGLE_CLOUD_API_KEY environment variable. Please enable YouTube Data API v3 in Google Cloud Console.');
        }
        
        // Initialize YouTube API client
        this.youtube = google.youtube({
            version: 'v3',
            auth: this.apiKey
        });
        
        console.log('✅ YouTube Data API v3 initialized successfully');
    }

    /**
     * Search for videos on YouTube
     * @param {string} query - Search query
     * @param {number} maxResults - Maximum number of results (default: 25, max: 50)
     * @param {string} order - Order of results (relevance, date, rating, title, videoCount, viewCount)
     * @returns {Promise<Object>} Search results
     */
    async searchVideos(query, maxResults = 25, order = 'relevance') {
        try {
            const response = await this.youtube.search.list({
                part: ['snippet'],
                q: query,
                type: 'video',
                maxResults: Math.min(maxResults, 50), // YouTube API limit
                order: order,
                safeSearch: 'moderate' // Important for spiritual content
            });

            return {
                success: true,
                data: response.data,
                videos: response.data.items.map(item => ({
                    id: item.id.videoId,
                    title: item.snippet.title,
                    description: item.snippet.description,
                    thumbnail: item.snippet.thumbnails.medium?.url || item.snippet.thumbnails.default?.url,
                    channelTitle: item.snippet.channelTitle,
                    publishedAt: item.snippet.publishedAt,
                    url: `https://www.youtube.com/watch?v=${item.id.videoId}`
                }))
            };
        } catch (error) {
            console.error('❌ YouTube search error:', error.message);
            return {
                success: false,
                error: error.message,
                videos: []
            };
        }
    }

    /**
     * Get detailed video information
     * @param {string|Array} videoId - Single video ID or array of video IDs
     * @returns {Promise<Object>} Video details
     */
    async getVideoDetails(videoId) {
        try {
            const ids = Array.isArray(videoId) ? videoId.join(',') : videoId;
            
            const response = await this.youtube.videos.list({
                part: ['snippet', 'statistics', 'contentDetails'],
                id: ids
            });

            return {
                success: true,
                data: response.data,
                videos: response.data.items.map(item => ({
                    id: item.id,
                    title: item.snippet.title,
                    description: item.snippet.description,
                    thumbnail: item.snippet.thumbnails.medium?.url || item.snippet.thumbnails.default?.url,
                    channelTitle: item.snippet.channelTitle,
                    publishedAt: item.snippet.publishedAt,
                    duration: item.contentDetails.duration,
                    viewCount: item.statistics.viewCount,
                    likeCount: item.statistics.likeCount,
                    commentCount: item.statistics.commentCount,
                    tags: item.snippet.tags || [],
                    url: `https://www.youtube.com/watch?v=${item.id}`
                }))
            };
        } catch (error) {
            console.error('❌ YouTube video details error:', error.message);
            return {
                success: false,
                error: error.message,
                videos: []
            };
        }
    }

    /**
     * Get channel information
     * @param {string} channelId - YouTube channel ID
     * @returns {Promise<Object>} Channel details
     */
    async getChannelInfo(channelId) {
        try {
            const response = await this.youtube.channels.list({
                part: ['snippet', 'statistics', 'contentDetails'],
                id: channelId
            });

            if (response.data.items.length === 0) {
                return { success: false, error: 'Channel not found', channel: null };
            }

            const channel = response.data.items[0];
            return {
                success: true,
                channel: {
                    id: channel.id,
                    title: channel.snippet.title,
                    description: channel.snippet.description,
                    thumbnail: channel.snippet.thumbnails.medium?.url || channel.snippet.thumbnails.default?.url,
                    subscriberCount: channel.statistics.subscriberCount,
                    videoCount: channel.statistics.videoCount,
                    viewCount: channel.statistics.viewCount,
                    publishedAt: channel.snippet.publishedAt,
                    uploadsPlaylistId: channel.contentDetails.relatedPlaylists.uploads
                }
            };
        } catch (error) {
            console.error('❌ YouTube channel info error:', error.message);
            return {
                success: false,
                error: error.message,
                channel: null
            };
        }
    }

    /**
     * Search for ACIM-related spiritual content (aligned with TestAlex mission)
     * @param {string} additionalTerms - Additional search terms to combine with ACIM
     * @param {number} maxResults - Maximum results (default: 10)
     * @returns {Promise<Object>} ACIM-related video results
     */
    async searchACIMContent(additionalTerms = '', maxResults = 10) {
        const acimTerms = [
            'A Course in Miracles',
            'ACIM',
            'Course in Miracles',
            'Kenneth Wapnick',
            'Helen Schucman',
            'Spiritual forgiveness',
            'Miracle principles'
        ];

        // Combine ACIM terms with additional search terms
        const searchQuery = additionalTerms 
            ? `${acimTerms[0]} ${additionalTerms}` 
            : acimTerms[Math.floor(Math.random() * acimTerms.length)];

        console.log(`🔍 Searching for ACIM content: "${searchQuery}"`);
        
        return await this.searchVideos(searchQuery, maxResults, 'relevance');
    }

    /**
     * Get video comments (requires OAuth for private videos)
     * @param {string} videoId - YouTube video ID
     * @param {number} maxResults - Maximum comments to retrieve
     * @returns {Promise<Object>} Video comments
     */
    async getVideoComments(videoId, maxResults = 20) {
        try {
            const response = await this.youtube.commentThreads.list({
                part: ['snippet'],
                videoId: videoId,
                maxResults: Math.min(maxResults, 100), // YouTube API limit
                order: 'time'
            });

            return {
                success: true,
                comments: response.data.items.map(item => ({
                    id: item.id,
                    text: item.snippet.topLevelComment.snippet.textDisplay,
                    author: item.snippet.topLevelComment.snippet.authorDisplayName,
                    publishedAt: item.snippet.topLevelComment.snippet.publishedAt,
                    likeCount: item.snippet.topLevelComment.snippet.likeCount,
                    replies: item.snippet.totalReplyCount
                }))
            };
        } catch (error) {
            console.error('❌ YouTube comments error:', error.message);
            return {
                success: false,
                error: error.message,
                comments: []
            };
        }
    }

    /**
     * Validate API key and quota
     * @returns {Promise<Object>} API validation result
     */
    async validateAPI() {
        try {
            // Simple test search to validate API key
            const testResponse = await this.youtube.search.list({
                part: ['snippet'],
                q: 'test',
                type: 'video',
                maxResults: 1
            });

            return {
                success: true,
                message: 'YouTube Data API v3 is working correctly',
                quotaUsed: true, // Each call uses quota
                apiVersion: 'v3'
            };
        } catch (error) {
            return {
                success: false,
                message: 'YouTube API validation failed',
                error: error.message,
                suggestions: [
                    'Ensure YouTube Data API v3 is enabled in Google Cloud Console',
                    'Check that GOOGLE_CLOUD_API_KEY is valid',
                    'Verify API key has proper restrictions configured'
                ]
            };
        }
    }
}

// Export for use in other modules
module.exports = YouTubeAPIManager;

// Example usage and testing
if (require.main === module) {
    async function testYouTubeAPI() {
        try {
            const ytAPI = new YouTubeAPIManager();
            
            console.log('\n🧪 Testing YouTube Data API v3...\n');
            
            // Test 1: API Validation
            console.log('1️⃣ Validating API...');
            const validation = await ytAPI.validateAPI();
            console.log(validation);
            
            if (!validation.success) {
                console.log('\n❌ API validation failed. Please check your configuration.');
                return;
            }
            
            // Test 2: Search for ACIM content (aligned with TestAlex spiritual mission)
            console.log('\n2️⃣ Searching for ACIM spiritual content...');
            const acimResults = await ytAPI.searchACIMContent('forgiveness', 5);
            if (acimResults.success) {
                console.log(`Found ${acimResults.videos.length} ACIM videos:`);
                acimResults.videos.forEach((video, index) => {
                    console.log(`  ${index + 1}. ${video.title} (${video.channelTitle})`);
                });
            }
            
            // Test 3: Get details for first video
            if (acimResults.success && acimResults.videos.length > 0) {
                console.log('\n3️⃣ Getting video details...');
                const videoDetails = await ytAPI.getVideoDetails(acimResults.videos[0].id);
                if (videoDetails.success && videoDetails.videos.length > 0) {
                    const video = videoDetails.videos[0];
                    console.log(`📺 "${video.title}"`);
                    console.log(`👁️  Views: ${parseInt(video.viewCount || 0).toLocaleString()}`);
                    console.log(`⏱️  Duration: ${video.duration}`);
                    console.log(`📅 Published: ${new Date(video.publishedAt).toLocaleDateString()}`);
                }
            }
            
            console.log('\n✅ YouTube API testing completed successfully!');
            console.log('\n📖 Next steps:');
            console.log('1. Integrate with your ACIMguide platform');
            console.log('2. Add spiritual content curation features');
            console.log('3. Implement user-friendly search interface');
            console.log('4. Consider rate limiting for production use');
            
        } catch (error) {
            console.error('❌ Test failed:', error.message);
        }
    }
    
    // Run tests
    testYouTubeAPI();
}
