/// <reference types="astro/client" />

declare namespace App {
  interface Locals {
    user?: {
      id: number;
      email: string;
      username: string;
      account_type: 'artist' | 'studio' | 'model';
      onboarding_completed: boolean;
      avatar_url?: string | null;
      banner_url?: string | null;
      created_at: string;
      updated_at: string;
    };
    sessionToken?: string;
  }
}

