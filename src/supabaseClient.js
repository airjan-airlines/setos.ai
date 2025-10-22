import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://wwanodyypltfnrukwknr.supabase.co';
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind3YW5vZHl5cGx0Zm5ydWt3a25yIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTU2NDcyOTcsImV4cCI6MjA3MTIyMzI5N30.MSeZZKY6UKHpMhK80SK1zMZGRW71Q9HPVfaeSwMuEaM';

export const supabase = createClient(supabaseUrl, supabaseAnonKey);
