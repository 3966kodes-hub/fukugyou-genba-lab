import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const posts = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/posts' }),
  schema: ({ image }) =>
    z.object({
      title: z.string(),
      description: z.string(),
      pubDate: z.coerce.date(),
      updatedDate: z.coerce.date().optional(),
      category: z.enum([
        'getting-started',
        'blog-writing',
        'video-audio',
        'creative',
        'programming',
        'retail',
        'investment',
        'skill-market',
        'tools',
        'ai-side-job',
        'real-experience',
      ]),
      tags: z.array(z.string()).default([]),
      heroImage: z.string().optional(),
      heroImageAlt: z.string().optional(),
      draft: z.boolean().default(false),
      featured: z.boolean().default(false),
      revenueRange: z
        .enum(['sub-1man', '1-5man', '5-10man', '10-30man', '30man-plus'])
        .optional(),
      difficulty: z.enum(['easy', 'medium', 'hard', 'expert']).optional(),
      isRealExperience: z.boolean().default(false),
      sources: z
        .array(
          z.object({
            label: z.string(),
            url: z.string().url(),
            author: z.string().optional(),
            quotedAt: z.coerce.date().optional(),
          }),
        )
        .default([]),
    }),
});

export const collections = { posts };
