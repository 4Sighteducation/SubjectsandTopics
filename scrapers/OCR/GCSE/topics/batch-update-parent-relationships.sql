-- ================================================================
-- Supabase Stored Procedure for Batch Updating Parent Relationships
-- ================================================================
-- This function allows efficient batch updates of parent_topic_id
-- Run this ONCE in your Supabase SQL Editor to enable batch updates
-- ================================================================

CREATE OR REPLACE FUNCTION batch_update_parent_relationships(
    updates JSONB
)
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    update_item JSONB;
    updated_count INTEGER := 0;
BEGIN
    -- Loop through each update in the JSONB array
    FOR update_item IN SELECT * FROM jsonb_array_elements(updates)
    LOOP
        UPDATE staging_aqa_topics
        SET parent_topic_id = (update_item->>'parent_topic_id')::uuid
        WHERE id = (update_item->>'id')::uuid;
        
        updated_count := updated_count + 1;
    END LOOP;
    
    RETURN updated_count;
END;
$$;

-- Grant execute permission to authenticated users
GRANT EXECUTE ON FUNCTION batch_update_parent_relationships(JSONB) TO authenticated;
GRANT EXECUTE ON FUNCTION batch_update_parent_relationships(JSONB) TO service_role;





















