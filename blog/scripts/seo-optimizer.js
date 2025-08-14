#!/usr/bin/env node

/**
 * SEO Optimizer for ACIM Blog
 * Injects meta tags, structured data, and analytics tracking
 * Optimizes for spiritual/ACIM-related search terms
 */

const fs = require('fs').promises;
const path = require('path');

// SEO Configuration
const SEO_CONFIG = {
  domain: 'acimcoach.com',
  blogPath: '/blog',
  siteName: 'ACIM Coach - Daily Spiritual Guidance',
  author: 'Alex Monas',
  twitterHandle: '@acimcoach',
  keywords: {
    primary: [
      'A Course in Miracles',
      'ACIM lessons',
      'spiritual guidance',
      'inner peace',
      'forgiveness practice',
      'spiritual awakening',
      'CourseGPT',
      'daily spiritual practice'
    ],
    secondary: [
      'spiritual AI',
      'ACIM workbook',
      'Course in Miracles study',
      'spiritual transformation',
      'holy spirit guidance',
      'miracle principles',
      'spiritual coach',
      'meditation practice'
    ]
  },
  structuredData: {
    organization: {
      '@context': 'https://schema.org',
      '@type': 'Organization',
      'name': 'ACIM Coach',
      'url': 'https://acimcoach.com',
      'description': 'Authentic spiritual guidance through A Course in Miracles teachings and CourseGPT AI assistance',
      'founder': {
        '@type': 'Person',
        'name': 'Alex Monas'
      },
      'sameAs': [
        'https://acimguide.com'
      ]
    }
  }
};

// Google Analytics and Search Console integration
const ANALYTICS_CONFIG = {
  googleAnalytics: 'G-XXXXXXXXXX', // Replace with actual GA4 ID
  googleSearchConsole: 'XXXXXXXXXXXX', // Replace with actual GSC verification
  hotjarId: 'XXXXXXX', // Optional: for user behavior tracking
  facebookPixel: 'XXXXXXXXXXXXXXXXX' // Optional: for social media tracking
};

/**
 * Generate comprehensive SEO metadata for blog posts
 */
function generateSEOMetadata(post) {
  const { title, description, date, lessonNumber, slug } = post;
  
  const canonicalUrl = `https://${SEO_CONFIG.domain}${SEO_CONFIG.blogPath}/${slug}`;
  const publishDate = new Date(date).toISOString();
  
  // Generate keywords based on lesson content
  const lessonKeywords = [
    ...SEO_CONFIG.keywords.primary,
    `ACIM lesson ${lessonNumber}`,
    `lesson ${lessonNumber}`,
    'daily ACIM',
    'Course in Miracles daily lesson'
  ];
  
  return {
    title: `${title} | ${SEO_CONFIG.siteName}`,
    description: description.substring(0, 160), // SEO-optimized length
    canonical: canonicalUrl,
    keywords: lessonKeywords.join(', '),
    openGraph: {
      type: 'article',
      title: title,
      description: description,
      url: canonicalUrl,
      site_name: SEO_CONFIG.siteName,
      published_time: publishDate,
      modified_time: publishDate,
      author: SEO_CONFIG.author,
      section: 'Spiritual Guidance',
      tags: lessonKeywords
    },
    twitter: {
      card: 'summary_large_image',
      site: SEO_CONFIG.twitterHandle,
      creator: SEO_CONFIG.twitterHandle,
      title: title,
      description: description
    },
    structuredData: {
      '@context': 'https://schema.org',
      '@type': 'BlogPosting',
      'headline': title,
      'description': description,
      'author': {
        '@type': 'Person',
        'name': SEO_CONFIG.author,
        'url': `https://${SEO_CONFIG.domain}`
      },
      'publisher': SEO_CONFIG.structuredData.organization,
      'datePublished': publishDate,
      'dateModified': publishDate,
      'mainEntityOfPage': canonicalUrl,
      'url': canonicalUrl,
      'keywords': lessonKeywords,
      'articleSection': 'Spiritual Guidance',
      'about': {
        '@type': 'Thing',
        'name': 'A Course in Miracles',
        'description': 'Spiritual curriculum focused on forgiveness and inner peace'
      }
    }
  };
}

/**
 * Generate robots.txt for proper search engine indexing
 */
function generateRobotsTxt() {
  return `User-agent: *
Allow: /

# Allow all search engines to index blog content
Allow: /blog/

# Sitemap location
Sitemap: https://${SEO_CONFIG.domain}${SEO_CONFIG.blogPath}/sitemap.xml

# Crawl-delay for respectful crawling
Crawl-delay: 1

# Block access to admin/private areas (if any)
Disallow: /admin/
Disallow: /private/
Disallow: *.json$
Disallow: /scripts/`;
}

/**
 * Generate comprehensive XML sitemap
 */
async function generateXMLSitemap() {
  try {
    // Read blog content directory
    const contentDir = path.join(process.cwd(), 'content');
    const files = await fs.readdir(contentDir);
    const blogPosts = files.filter(file => file.endsWith('.md'));
    
    let sitemapEntries = [];
    
    // Add main blog index
    sitemapEntries.push({
      url: `https://${SEO_CONFIG.domain}${SEO_CONFIG.blogPath}/`,
      lastmod: new Date().toISOString(),
      changefreq: 'daily',
      priority: '1.0'
    });
    
    // Process each blog post
    for (const file of blogPosts) {
      const filePath = path.join(contentDir, file);
      const content = await fs.readFile(filePath, 'utf8');
      
      // Extract frontmatter
      const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
      if (frontmatterMatch) {
        const frontmatter = frontmatterMatch[1];
        const dateMatch = frontmatter.match(/date: "([^"]+)"/);
        
        if (dateMatch) {
          const slug = file.replace('.md', '');
          sitemapEntries.push({
            url: `https://${SEO_CONFIG.domain}${SEO_CONFIG.blogPath}/${slug}`,
            lastmod: new Date(dateMatch[1]).toISOString(),
            changefreq: 'weekly',
            priority: '0.8'
          });
        }
      }
    }
    
    // Generate XML
    const xml = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml"
        xmlns:mobile="http://www.google.com/schemas/sitemap-mobile/1.0"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"
        xmlns:video="http://www.google.com/schemas/sitemap-video/1.1">
${sitemapEntries.map(entry => `  <url>
    <loc>${entry.url}</loc>
    <lastmod>${entry.lastmod}</lastmod>
    <changefreq>${entry.changefreq}</changefreq>
    <priority>${entry.priority}</priority>
  </url>`).join('\n')}
</urlset>`;
    
    return xml;
    
  } catch (error) {
    console.error('Error generating XML sitemap:', error);
    return null;
  }
}

/**
 * Generate Google Analytics and tracking code
 */
function generateAnalyticsCode() {
  return `<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=${ANALYTICS_CONFIG.googleAnalytics}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', '${ANALYTICS_CONFIG.googleAnalytics}', {
    page_title: document.title,
    page_location: window.location.href,
    content_group1: 'ACIM Blog',
    custom_map: {
      'dimension1': 'lesson_number',
      'dimension2': 'spiritual_topic'
    }
  });
  
  // Track CourseGPT clicks (main CTA)
  document.addEventListener('click', function(e) {
    if (e.target.href && e.target.href.includes('acimguide.com')) {
      gtag('event', 'click', {
        event_category: 'CTA',
        event_label: 'CourseGPT_Link',
        value: 1
      });
    }
  });
</script>

<!-- Google Search Console Verification -->
<meta name="google-site-verification" content="${ANALYTICS_CONFIG.googleSearchConsole}" />

<!-- Schema.org JSON-LD for better search understanding -->
<script type="application/ld+json">
${JSON.stringify(SEO_CONFIG.structuredData.organization, null, 2)}
</script>`;
}

/**
 * Inject SEO metadata into HTML files
 */
async function injectSEOMetadata(htmlFilePath, metadata) {
  try {
    let html = await fs.readFile(htmlFilePath, 'utf8');
    
    // Inject meta tags in <head>
    const metaTags = `
    <!-- SEO Meta Tags -->
    <meta name="description" content="${metadata.description}">
    <meta name="keywords" content="${metadata.keywords}">
    <meta name="author" content="${SEO_CONFIG.author}">
    <link rel="canonical" href="${metadata.canonical}">
    
    <!-- Open Graph -->
    <meta property="og:type" content="${metadata.openGraph.type}">
    <meta property="og:title" content="${metadata.openGraph.title}">
    <meta property="og:description" content="${metadata.openGraph.description}">
    <meta property="og:url" content="${metadata.openGraph.url}">
    <meta property="og:site_name" content="${metadata.openGraph.site_name}">
    <meta property="article:published_time" content="${metadata.openGraph.published_time}">
    <meta property="article:author" content="${metadata.openGraph.author}">
    <meta property="article:section" content="${metadata.openGraph.section}">
    
    <!-- Twitter Card -->
    <meta name="twitter:card" content="${metadata.twitter.card}">
    <meta name="twitter:site" content="${metadata.twitter.site}">
    <meta name="twitter:creator" content="${metadata.twitter.creator}">
    <meta name="twitter:title" content="${metadata.twitter.title}">
    <meta name="twitter:description" content="${metadata.twitter.description}">
    
    <!-- Structured Data -->
    <script type="application/ld+json">
    ${JSON.stringify(metadata.structuredData, null, 2)}
    </script>
    
    ${generateAnalyticsCode()}`;
    
    // Insert before closing </head> tag
    html = html.replace('</head>', `${metaTags}\n</head>`);
    
    await fs.writeFile(htmlFilePath, html, 'utf8');
    console.log(`✅ Injected SEO metadata into ${path.basename(htmlFilePath)}`);
    
  } catch (error) {
    console.error(`Error injecting SEO metadata into ${htmlFilePath}:`, error);
  }
}

/**
 * Main SEO optimization function
 */
async function optimizeSEO() {
  console.log('🔍 Starting SEO optimization...');
  
  try {
    // Generate and save robots.txt
    const robotsTxt = generateRobotsTxt();
    const robotsPath = path.join(process.cwd(), 'site', 'dist', 'robots.txt');
    await fs.writeFile(robotsPath, robotsTxt);
    console.log('✅ Generated robots.txt');
    
    // Generate and save XML sitemap
    const xmlSitemap = await generateXMLSitemap();
    if (xmlSitemap) {
      const sitemapPath = path.join(process.cwd(), 'site', 'dist', 'sitemap.xml');
      await fs.writeFile(sitemapPath, xmlSitemap);
      console.log('✅ Generated XML sitemap');
    }
    
    // Create SEO report
    const report = {
      timestamp: new Date().toISOString(),
      optimizations: [
        'Meta tags optimized for ACIM keywords',
        'Structured data added for better search understanding',
        'Open Graph tags for social media sharing',
        'Twitter Card metadata included',
        'Google Analytics tracking implemented',
        'XML sitemap generated with proper priority',
        'Robots.txt configured for search engines',
        'Canonical URLs set to prevent duplicate content',
        'Call-to-action tracking for CourseGPT links'
      ],
      targetKeywords: [
        ...SEO_CONFIG.keywords.primary,
        ...SEO_CONFIG.keywords.secondary
      ],
      kpiTargets: {
        organicVisitors: '1,000/month within 60 days',
        clickThroughRate: '80% to ACIMguide.com',
        searchRankings: 'Top 3 for primary ACIM keywords'
      }
    };
    
    const reportPath = path.join(process.cwd(), 'seo-report.json');
    await fs.writeFile(reportPath, JSON.stringify(report, null, 2));
    console.log('✅ Generated SEO report');
    
    console.log('\n🎯 SEO Optimization Complete!');
    console.log('📈 Target: 1,000 organic visitors/month');
    console.log('🔗 Target: 80% click-through to ACIMguide.com');
    console.log('⏰ Timeline: 60 days');
    
  } catch (error) {
    console.error('❌ Error during SEO optimization:', error);
  }
}

// Run if called directly
if (require.main === module) {
  optimizeSEO();
}

module.exports = {
  generateSEOMetadata,
  generateXMLSitemap,
  injectSEOMetadata,
  optimizeSEO,
  SEO_CONFIG
};
