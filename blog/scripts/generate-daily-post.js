#!/usr/bin/env node

/**
 * ACIM Daily Blog Post Generator
 * Generates markdown posts from ACIM lesson templates
 * Stores in blog/content/{YYYY-MM-DD}.md format
 */

const fs = require('fs').promises;
const path = require('path');

// ACIM Lesson Data (sample - would be extended to all 365 lessons)
const ACIM_LESSONS = {
  1: {
    title: 'Nothing I see means anything',
    content: `The first lesson of A Course in Miracles begins our journey toward true vision. When the Course states "Nothing I see in this room [on this street, from this window, in this place] means anything," it's not asking us to dismiss the world but to recognize that our interpretations give everything its meaning.

This lesson challenges our fundamental assumptions about reality. We believe we see objects, people, and situations that have inherent meaning, but the Course teaches us that meaning is something we assign, not something that exists independently.

## Understanding Today's Lesson

The lesson asks us to look around and apply this idea to whatever we see:
- Nothing I see in this room means anything
- Nothing I see on this street means anything  
- Nothing I see from this window means anything

This isn't nihilism - it's preparation for true seeing. By releasing our preconceptions, we open space for the Holy Spirit's interpretation.

## Practical Application with CourseGPT

Many students find this first lesson challenging. The ego mind rebels against the suggestion that our perceptions might be meaningless. CourseGPT can help you explore your resistance to this idea and guide you toward the peace that comes with letting go of the need to make everything mean something according to your personal story.

> "Nothing I see in this room [on this street, from this window, in this place] means anything." (W-pI.1.3:1)

The power of this lesson lies not in understanding it intellectually, but in practicing it with willingness. Each time you apply the idea, you're taking a step away from the ego's world of separate meanings toward the unified vision of love.`
  },
  2: {
    title: 'I have given everything I see all the meaning that it has for me',
    content: `Today's lesson builds directly on yesterday's recognition that nothing we see has inherent meaning. Now we take responsibility for the meanings we've assigned to everything in our experience.

This is perhaps one of the most liberating recognitions in the Course: you are not at the mercy of external circumstances because you are the one giving them their meaning. The situation itself is neutral - your interpretation makes it "good" or "bad," "threatening" or "safe."

## Understanding Today's Lesson

When you look at anything today - a person, object, or situation - remind yourself:
- I have given this desk all the meaning it has for me
- I have given that person all the meaning they have for me
- I have given this situation all the meaning it has for me

This isn't about blame or guilt. It's about recognizing your power to choose your interpretation, and therefore your experience.

## The Freedom in Responsibility

Taking responsibility for the meanings you assign might initially feel heavy, but it's actually the key to freedom. If you gave something its meaning, you can give it a different meaning. If you made someone into an enemy, you can see them differently. If you decided a situation was hopeless, you can choose hope.

## Practical Application with CourseGPT

CourseGPT can help you identify the meanings you've unconsciously assigned to people and situations in your life. Often we don't realize how many judgments and interpretations we're carrying. Through gentle questioning, CourseGPT can help you see these patterns and choose differently.

> "I have given everything I see in this room [on this street, from this window, in this place] all the meaning that it has for me." (W-pI.2.1:1)`
  }
};

const SEO_KEYWORDS = [
  'ACIM lesson',
  'A Course in Miracles',
  'daily spiritual guidance',
  'spiritual practice',
  'inner peace',
  'forgiveness practice',
  'CourseGPT',
  'spiritual awakening'
];

function getCurrentDate() {
  const now = new Date();
  return {
    year: now.getFullYear(),
    month: String(now.getMonth() + 1).padStart(2, '0'),
    day: String(now.getDate()).padStart(2, '0'),
    dateString: `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
  };
}

function getLessonForDate(dateString) {
  // Simple rotation through lessons 1-365
  const startDate = new Date('2024-01-01');
  const currentDate = new Date(dateString);
  const daysDiff = Math.floor((currentDate - startDate) / (1000 * 60 * 60 * 24));
  const lessonNumber = (daysDiff % 365) + 1;
  
  // For demo, we only have lessons 1-2, so cycle between them
  return lessonNumber <= 2 ? lessonNumber : ((lessonNumber - 1) % 2) + 1;
}

function generateSEOMetadata(lesson, lessonNumber, date) {
  return {
    title: `ACIM Lesson ${lessonNumber}: ${lesson.title} - Daily Spiritual Guidance`,
    description: `Explore today's A Course in Miracles lesson with deep spiritual insights. Practice authentic forgiveness and find inner peace through ACIM teachings. Free guidance with CourseGPT at ACIMguide.com`,
    keywords: [...SEO_KEYWORDS, lesson.title, `lesson ${lessonNumber}`, 'ACIM workbook'],
    canonicalUrl: `https://acimcoach.com/blog/${date}`,
    openGraph: {
      type: 'article',
      title: `ACIM Lesson ${lessonNumber}: ${lesson.title}`,
      description: `Daily spiritual guidance from A Course in Miracles. Find inner peace and practice true forgiveness with today's lesson insights.`,
      url: `https://acimcoach.com/blog/${date}`,
      siteName: 'ACIM Coach - Spiritual Guidance Blog',
      publishedTime: new Date().toISOString(),
      modifiedTime: new Date().toISOString(),
      author: 'Alex Monas',
      section: 'Spiritual Guidance',
      tags: SEO_KEYWORDS
    }
  };
}

async function generateBlogPost() {
  const date = getCurrentDate();
  const lessonNumber = getLessonForDate(date.dateString);
  const lesson = ACIM_LESSONS[lessonNumber];
  
  if (!lesson) {
    throw new Error(`Lesson ${lessonNumber} not found in database`);
  }

  const metadata = generateSEOMetadata(lesson, lessonNumber, date.dateString);
  
  const frontMatter = `---
title: "${metadata.title}"
description: "${metadata.description}"
date: "${new Date().toISOString()}"
slug: "${date.dateString}"
lesson_number: ${lessonNumber}
categories:
  - "ACIM Lessons"
  - "Daily Spiritual Guidance"
  - "A Course in Miracles"
tags:
  ${metadata.keywords.map(keyword => `- "${keyword}"`).join('\n  ')}
seo:
  canonical_url: "${metadata.canonicalUrl}"
  og_type: "article"
  og_title: "${metadata.openGraph.title}"
  og_description: "${metadata.openGraph.description}"
  og_url: "${metadata.openGraph.url}"
  og_site_name: "${metadata.openGraph.siteName}"
  article_published_time: "${metadata.openGraph.publishedTime}"
  article_modified_time: "${metadata.openGraph.modifiedTime}"
  article_author: "${metadata.openGraph.author}"
  article_section: "${metadata.openGraph.section}"
  article_tags: [${metadata.openGraph.tags.map(tag => `"${tag}"`).join(', ')}]
---`;

  const callToAction = `
## Experience Deeper ACIM Guidance

Ready to deepen your understanding of A Course in Miracles? Visit **[ACIMguide.com](https://acimguide.com)** for unlimited conversations with CourseGPT, your AI spiritual companion trained exclusively on ACIM teachings.

### Why Choose CourseGPT?

- **Authentic ACIM Guidance**: Responses based solely on Course principles
- **24/7 Spiritual Support**: Available whenever you need guidance
- **Personalized Learning**: Adapts to your unique spiritual journey
- **Free to Start**: Begin your transformation today

[**Start Your Free Session with CourseGPT →**](https://acimguide.com)

---

*Transform your spiritual practice with authentic A Course in Miracles guidance. Join thousands discovering inner peace through CourseGPT at ACIMguide.com*`;

  const fullPost = `${frontMatter}

# ACIM Lesson ${lessonNumber}: ${lesson.title}

${lesson.content}

${callToAction}`;

  return {
    content: fullPost,
    filename: `${date.dateString}.md`,
    metadata: {
      date: date.dateString,
      lessonNumber,
      title: lesson.title,
      seo: metadata
    }
  };
}

async function ensureDirectoryExists(dirPath) {
  try {
    await fs.mkdir(dirPath, { recursive: true });
  } catch (error) {
    if (error.code !== 'EEXIST') {
      throw error;
    }
  }
}

async function main() {
  try {
    console.log('🔮 Generating daily ACIM blog post...');
    
    const post = await generateBlogPost();
    // Adjust path based on current working directory
    const isInScriptsDir = process.cwd().endsWith('scripts');
    const contentDir = isInScriptsDir 
      ? path.join(process.cwd(), '..', 'content')
      : path.join(process.cwd(), 'blog', 'content');
    
    await ensureDirectoryExists(contentDir);
    
    const filePath = path.join(contentDir, post.filename);
    await fs.writeFile(filePath, post.content, 'utf8');
    
    console.log(`✅ Generated blog post: ${post.filename}`);
    console.log(`📝 Lesson ${post.metadata.lessonNumber}: ${post.metadata.title}`);
    console.log(`📍 Saved to: ${filePath}`);
    console.log(`🔗 Will be available at: https://acimcoach.com/blog/${post.metadata.date}`);
    
    // Update sitemap and meta information
    await updateSitemap(post.metadata);
    
  } catch (error) {
    console.error('❌ Error generating blog post:', error.message);
    process.exit(1);
  }
}

async function updateSitemap(postMetadata) {
  try {
    // Adjust path based on current working directory
    const isInScriptsDir = process.cwd().endsWith('scripts');
    const sitemapPath = isInScriptsDir
      ? path.join(process.cwd(), '..', 'sitemap.json')
      : path.join(process.cwd(), 'blog', 'sitemap.json');
    let sitemap = [];
    
    try {
      const existing = await fs.readFile(sitemapPath, 'utf8');
      sitemap = JSON.parse(existing);
    } catch (error) {
      // File doesn't exist yet, start with empty array
    }
    
    // Add new post to sitemap
    const newEntry = {
      url: `https://acimcoach.com/blog/${postMetadata.date}`,
      lastmod: new Date().toISOString(),
      changefreq: 'weekly',
      priority: 0.8,
      metadata: {
        title: postMetadata.seo.title,
        description: postMetadata.seo.description,
        lessonNumber: postMetadata.lessonNumber
      }
    };
    
    // Remove existing entry for this date if it exists
    sitemap = sitemap.filter(entry => !entry.url.includes(postMetadata.date));
    sitemap.unshift(newEntry);
    
    // Keep only last 100 entries to prevent sitemap from becoming too large
    sitemap = sitemap.slice(0, 100);
    
    await fs.writeFile(sitemapPath, JSON.stringify(sitemap, null, 2));
    console.log('🗺️ Updated sitemap.json');
    
  } catch (error) {
    console.error('⚠️ Warning: Could not update sitemap:', error.message);
  }
}

if (require.main === module) {
  main();
}

module.exports = { generateBlogPost, getLessonForDate };
