# 🚨 URGENT: Firebase API Key Regeneration Guide

## ⚠️ CRITICAL SECURITY ACTION REQUIRED

Your Firebase API key `AIzaSyCyGw7AioVfQ3sfxlW1kWnlsNnrQAmymwU` was exposed in your public GitHub repository and MUST be regenerated immediately to prevent unauthorized usage.

## 🔑 Step-by-Step API Key Regeneration

### 1. Access Google Cloud Console
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project: `acim-guide-test`
3. Navigate to **APIs & Services** → **Credentials**

### 2. Locate the Exposed API Key
1. Find the API key `AIzaSyCyGw7AioVfQ3sfxlW1kWnlsNnrQAmymwU`
2. Click on the key name to view details
3. **IMMEDIATELY DELETE** this compromised key by clicking "Delete"

### 3. Create New API Key
1. Click **"+ CREATE CREDENTIALS"** → **API Key**
2. A new API key will be generated
3. **COPY** the new key immediately (you won't see it again)
4. Click **"RESTRICT KEY"** to add security restrictions

### 4. Configure API Key Restrictions
**Application restrictions:**
- Select **"HTTP referrers (web sites)"**
- Add these referrers:
  - `https://acim-guide-test.web.app/*`
  - `https://acim-guide-test.firebaseapp.com/*`
  - `http://localhost:*` (for development)
  - Add your custom domain if you have one

**API restrictions:**
- Select **"Restrict key"**
- Enable only these APIs:
  - Firebase Hosting API
  - Firebase Realtime Database API
  - Cloud Firestore API
  - Firebase Authentication API

### 5. Update Your Environment Configuration
1. Update your local `.env` file:
   ```bash
   FIREBASE_API_KEY=your_new_api_key_here
   ```
2. Update any deployment scripts or configuration files
3. **NEVER** commit the API key to version control

### 6. Deploy with New API Key
Use the secure deployment script we created:
```bash
# Set the environment variable
export FIREBASE_API_KEY="your_new_api_key_here"

# Run the secure deployment
./secure-deploy.sh
```

## 🔍 Security Audit Steps

### Check for Unauthorized Usage
1. In Google Cloud Console, go to **APIs & Services** → **Quotas**
2. Review API usage for unusual patterns
3. Check **Billing** → **Reports** for unexpected charges
4. Look for API calls from unknown IP addresses or domains

### Monitor Going Forward
1. Set up billing alerts in Google Cloud Console
2. Enable API usage monitoring and alerts
3. Regular review of API access logs
4. Consider rotating API keys every 90 days

## 🚨 Immediate Actions Checklist

- [ ] **Delete the compromised API key** `AIzaSyCyGw7AioVfQ3sfxlW1kWnlsNnrQAmymwU`
- [ ] **Create new API key** with proper restrictions
- [ ] **Restrict API key** to your domains and required APIs only
- [ ] **Update environment configuration** with new key
- [ ] **Test application** with new API key
- [ ] **Audit billing** for unauthorized usage
- [ ] **Monitor usage** for next 30 days

## 🛡️ Prevention Measures

### For Future Development
1. **Always use environment variables** for API keys
2. **Never commit .env files** to version control
3. **Use the secure deployment script** we created
4. **Regular security audits** of repository for exposed secrets
5. **Rotate API keys** every 90 days as best practice

### Repository Security
- The CI/CD pipeline now scans for exposed secrets
- .env files are properly ignored in .gitignore
- Secure deployment process prevents future exposure

## ⏰ Urgency Level: CRITICAL

**Time to complete:** 15-20 minutes  
**Risk if delayed:** Unauthorized API usage and potential charges  
**Status:** The code repository is secure, but the API key itself remains active until regenerated

## 📞 If You Need Help

If you encounter any issues during the regeneration process:

1. **Google Cloud Support**: Available in the console
2. **Firebase Support**: [Firebase Help Center](https://firebase.google.com/support)
3. **Emergency**: If you see suspicious activity, immediately disable the key

## 🙏 After Completion

Once you've regenerated the API key:
1. Test the application thoroughly
2. Monitor for any authentication errors  
3. Update any team members who may have the old key
4. Consider implementing additional security measures like IP restrictions

---

**Remember:** This is a critical security issue that requires immediate attention. The compromised key must be regenerated today to prevent potential unauthorized usage of your Firebase services.

The repository security has been fully resolved, but the actual API key in Google Cloud Console needs your direct action to regenerate and restrict properly.
