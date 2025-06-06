

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;


CREATE SCHEMA IF NOT EXISTS "basejump";


ALTER SCHEMA "basejump" OWNER TO "postgres";


COMMENT ON SCHEMA "public" IS 'standard public schema';



CREATE EXTENSION IF NOT EXISTS "pg_graphql" WITH SCHEMA "graphql";






CREATE EXTENSION IF NOT EXISTS "pg_stat_statements" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pgcrypto" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pgjwt" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "supabase_vault" WITH SCHEMA "vault";






CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA "extensions";






CREATE TYPE "basejump"."account_role" AS ENUM (
    'owner',
    'member'
);


ALTER TYPE "basejump"."account_role" OWNER TO "postgres";


CREATE TYPE "basejump"."invitation_type" AS ENUM (
    'one_time',
    '24_hour'
);


ALTER TYPE "basejump"."invitation_type" OWNER TO "postgres";


CREATE TYPE "basejump"."subscription_status" AS ENUM (
    'trialing',
    'active',
    'canceled',
    'incomplete',
    'incomplete_expired',
    'past_due',
    'unpaid'
);


ALTER TYPE "basejump"."subscription_status" OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "basejump"."add_current_user_to_new_account"() RETURNS "trigger"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
begin
    if new.primary_owner_user_id = auth.uid() then
        insert into basejump.account_user (account_id, user_id, account_role)
        values (NEW.id, auth.uid(), 'owner');
    end if;
    return NEW;
end;
$$;


ALTER FUNCTION "basejump"."add_current_user_to_new_account"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "basejump"."generate_token"("length" integer) RETURNS "text"
    LANGUAGE "sql"
    AS $$
select regexp_replace(replace(
                              replace(replace(replace(encode(gen_random_bytes(length)::bytea, 'base64'), '/', ''), '+',
                                              ''), '\', ''),
                              '=',
                              ''), E'[\\n\\r]+', '', 'g');
$$;


ALTER FUNCTION "basejump"."generate_token"("length" integer) OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "basejump"."get_accounts_with_role"("passed_in_role" "basejump"."account_role" DEFAULT NULL::"basejump"."account_role") RETURNS SETOF "uuid"
    LANGUAGE "sql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
select account_id
from basejump.account_user wu
where wu.user_id = auth.uid()
  and (
            wu.account_role = passed_in_role
        or passed_in_role is null
    );
$$;


ALTER FUNCTION "basejump"."get_accounts_with_role"("passed_in_role" "basejump"."account_role") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "basejump"."get_config"() RETURNS "json"
    LANGUAGE "plpgsql"
    AS $$
DECLARE
    result RECORD;
BEGIN
    SELECT * from basejump.config limit 1 into result;
    return row_to_json(result);
END;
$$;


ALTER FUNCTION "basejump"."get_config"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "basejump"."has_role_on_account"("account_id" "uuid", "account_role" "basejump"."account_role" DEFAULT NULL::"basejump"."account_role") RETURNS boolean
    LANGUAGE "sql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
select exists(
               select 1
               from basejump.account_user wu
               where wu.user_id = auth.uid()
                 and wu.account_id = has_role_on_account.account_id
                 and (
                           wu.account_role = has_role_on_account.account_role
                       or has_role_on_account.account_role is null
                   )
           );
$$;


ALTER FUNCTION "basejump"."has_role_on_account"("account_id" "uuid", "account_role" "basejump"."account_role") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "basejump"."is_set"("field_name" "text") RETURNS boolean
    LANGUAGE "plpgsql"
    AS $$
DECLARE
    result BOOLEAN;
BEGIN
    execute format('select %I from basejump.config limit 1', field_name) into result;
    return result;
END;
$$;


ALTER FUNCTION "basejump"."is_set"("field_name" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "basejump"."protect_account_fields"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    IF current_user IN ('authenticated', 'anon') THEN
        -- these are protected fields that users are not allowed to update themselves
        -- platform admins should be VERY careful about updating them as well.
        if NEW.id <> OLD.id
            OR NEW.personal_account <> OLD.personal_account
            OR NEW.primary_owner_user_id <> OLD.primary_owner_user_id
        THEN
            RAISE EXCEPTION 'You do not have permission to update this field';
        end if;
    end if;

    RETURN NEW;
END
$$;


ALTER FUNCTION "basejump"."protect_account_fields"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "basejump"."run_new_user_setup"() RETURNS "trigger"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
declare
    first_account_id    uuid;
    generated_user_name text;
begin

    -- first we setup the user profile
    -- TODO: see if we can get the user's name from the auth.users table once we learn how oauth works
    if new.email IS NOT NULL then
        generated_user_name := split_part(new.email, '@', 1);
    end if;
    -- create the new users's personal account
    insert into basejump.accounts (name, primary_owner_user_id, personal_account, id)
    values (generated_user_name, NEW.id, true, NEW.id)
    returning id into first_account_id;

    -- add them to the account_user table so they can act on it
    insert into basejump.account_user (account_id, user_id, account_role)
    values (first_account_id, NEW.id, 'owner');

    return NEW;
end;
$$;


ALTER FUNCTION "basejump"."run_new_user_setup"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "basejump"."slugify_account_slug"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    if NEW.slug is not null then
        NEW.slug = lower(regexp_replace(NEW.slug, '[^a-zA-Z0-9-]+', '-', 'g'));
    end if;

    RETURN NEW;
END
$$;


ALTER FUNCTION "basejump"."slugify_account_slug"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "basejump"."trigger_set_invitation_details"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    NEW.invited_by_user_id = auth.uid();
    NEW.account_name = (select name from basejump.accounts where id = NEW.account_id);
    RETURN NEW;
END
$$;


ALTER FUNCTION "basejump"."trigger_set_invitation_details"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "basejump"."trigger_set_timestamps"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    if TG_OP = 'INSERT' then
        NEW.created_at = now();
        NEW.updated_at = now();
    else
        NEW.updated_at = now();
        NEW.created_at = OLD.created_at;
    end if;
    RETURN NEW;
END
$$;


ALTER FUNCTION "basejump"."trigger_set_timestamps"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "basejump"."trigger_set_user_tracking"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    if TG_OP = 'INSERT' then
        NEW.created_by = auth.uid();
        NEW.updated_by = auth.uid();
    else
        NEW.updated_by = auth.uid();
        NEW.created_by = OLD.created_by;
    end if;
    RETURN NEW;
END
$$;


ALTER FUNCTION "basejump"."trigger_set_user_tracking"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."accept_invitation"("lookup_invitation_token" "text") RETURNS "jsonb"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public', 'basejump'
    AS $$
declare
    lookup_account_id       uuid;
    declare new_member_role basejump.account_role;
    lookup_account_slug     text;
begin
    select i.account_id, i.account_role, a.slug
    into lookup_account_id, new_member_role, lookup_account_slug
    from basejump.invitations i
             join basejump.accounts a on a.id = i.account_id
    where i.token = lookup_invitation_token
      and i.created_at > now() - interval '24 hours';

    if lookup_account_id IS NULL then
        raise exception 'Invitation not found';
    end if;

    if lookup_account_id is not null then
        -- we've validated the token is real, so grant the user access
        insert into basejump.account_user (account_id, user_id, account_role)
        values (lookup_account_id, auth.uid(), new_member_role);
        -- email types of invitations are only good for one usage
        delete from basejump.invitations where token = lookup_invitation_token and invitation_type = 'one_time';
    end if;
    return json_build_object('account_id', lookup_account_id, 'account_role', new_member_role, 'slug',
                             lookup_account_slug);
EXCEPTION
    WHEN unique_violation THEN
        raise exception 'You are already a member of this account';
end;
$$;


ALTER FUNCTION "public"."accept_invitation"("lookup_invitation_token" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."add_agent_to_library"("p_original_agent_id" "uuid", "p_user_account_id" "uuid") RETURNS "uuid"
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
DECLARE
    v_new_agent_id UUID;
    v_original_agent agents%ROWTYPE;
BEGIN
    SELECT * INTO v_original_agent
    FROM agents 
    WHERE agent_id = p_original_agent_id AND is_public = true;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Agent not found or not public';
    END IF;
    
    IF EXISTS (
        SELECT 1 FROM user_agent_library 
        WHERE user_account_id = p_user_account_id 
        AND original_agent_id = p_original_agent_id
    ) THEN
        RAISE EXCEPTION 'Agent already in your library';
    END IF;
    
    INSERT INTO agents (
        account_id,
        name,
        description,
        system_prompt,
        configured_mcps,
        agentpress_tools,
        is_default,
        is_public,
        tags,
        avatar,
        avatar_color
    ) VALUES (
        p_user_account_id,
        v_original_agent.name || ' (from marketplace)',
        v_original_agent.description,
        v_original_agent.system_prompt,
        v_original_agent.configured_mcps,
        v_original_agent.agentpress_tools,
        false,
        false,
        v_original_agent.tags,
        v_original_agent.avatar,
        v_original_agent.avatar_color
    ) RETURNING agent_id INTO v_new_agent_id;
    
    INSERT INTO user_agent_library (
        user_account_id,
        original_agent_id,
        agent_id
    ) VALUES (
        p_user_account_id,
        p_original_agent_id,
        v_new_agent_id
    );
    
    UPDATE agents 
    SET download_count = download_count + 1 
    WHERE agent_id = p_original_agent_id;
    
    RETURN v_new_agent_id;
END;
$$;


ALTER FUNCTION "public"."add_agent_to_library"("p_original_agent_id" "uuid", "p_user_account_id" "uuid") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."create_account"("slug" "text" DEFAULT NULL::"text", "name" "text" DEFAULT NULL::"text") RETURNS "json"
    LANGUAGE "plpgsql"
    AS $$
DECLARE
    new_account_id uuid;
BEGIN
    insert into basejump.accounts (slug, name)
    values (create_account.slug, create_account.name)
    returning id into new_account_id;

    return public.get_account(new_account_id);
EXCEPTION
    WHEN unique_violation THEN
        raise exception 'An account with that unique ID already exists';
END;
$$;


ALTER FUNCTION "public"."create_account"("slug" "text", "name" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."create_invitation"("account_id" "uuid", "account_role" "basejump"."account_role", "invitation_type" "basejump"."invitation_type") RETURNS "json"
    LANGUAGE "plpgsql"
    AS $$
declare
    new_invitation basejump.invitations;
begin
    insert into basejump.invitations (account_id, account_role, invitation_type, invited_by_user_id)
    values (account_id, account_role, invitation_type, auth.uid())
    returning * into new_invitation;

    return json_build_object('token', new_invitation.token);
end
$$;


ALTER FUNCTION "public"."create_invitation"("account_id" "uuid", "account_role" "basejump"."account_role", "invitation_type" "basejump"."invitation_type") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."current_user_account_role"("account_id" "uuid") RETURNS "jsonb"
    LANGUAGE "plpgsql"
    AS $$
DECLARE
    response jsonb;
BEGIN

    select jsonb_build_object(
                   'account_role', wu.account_role,
                   'is_primary_owner', a.primary_owner_user_id = auth.uid(),
                   'is_personal_account', a.personal_account
               )
    into response
    from basejump.account_user wu
             join basejump.accounts a on a.id = wu.account_id
    where wu.user_id = auth.uid()
      and wu.account_id = current_user_account_role.account_id;

    -- if the user is not a member of the account, throw an error
    if response ->> 'account_role' IS NULL then
        raise exception 'Not found';
    end if;

    return response;
END
$$;


ALTER FUNCTION "public"."current_user_account_role"("account_id" "uuid") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."delete_invitation"("invitation_id" "uuid") RETURNS "void"
    LANGUAGE "plpgsql"
    AS $$
begin
    -- verify account owner for the invitation
    if basejump.has_role_on_account(
               (select account_id from basejump.invitations where id = delete_invitation.invitation_id), 'owner') <>
       true then
        raise exception 'Only account owners can delete invitations';
    end if;

    delete from basejump.invitations where id = delete_invitation.invitation_id;
end
$$;


ALTER FUNCTION "public"."delete_invitation"("invitation_id" "uuid") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_account"("account_id" "uuid") RETURNS "json"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    -- check if the user is a member of the account or a service_role user
    if current_user IN ('anon', 'authenticated') and
       (select current_user_account_role(get_account.account_id) ->> 'account_role' IS NULL) then
        raise exception 'You must be a member of an account to access it';
    end if;


    return (select json_build_object(
                           'account_id', a.id,
                           'account_role', wu.account_role,
                           'is_primary_owner', a.primary_owner_user_id = auth.uid(),
                           'name', a.name,
                           'slug', a.slug,
                           'personal_account', a.personal_account,
                           'billing_enabled', case
                                                  when a.personal_account = true then
                                                      config.enable_personal_account_billing
                                                  else
                                                      config.enable_team_account_billing
                               end,
                           'billing_status', bs.status,
                           'created_at', a.created_at,
                           'updated_at', a.updated_at,
                           'metadata', a.public_metadata
                       )
            from basejump.accounts a
                     left join basejump.account_user wu on a.id = wu.account_id and wu.user_id = auth.uid()
                     join basejump.config config on true
                     left join (select bs.account_id, status
                                from basejump.billing_subscriptions bs
                                where bs.account_id = get_account.account_id
                                order by created desc
                                limit 1) bs on bs.account_id = a.id
            where a.id = get_account.account_id);
END;
$$;


ALTER FUNCTION "public"."get_account"("account_id" "uuid") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_account_billing_status"("account_id" "uuid") RETURNS "jsonb"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public', 'basejump'
    AS $$
DECLARE
    result      jsonb;
    role_result jsonb;
BEGIN
    select public.current_user_account_role(get_account_billing_status.account_id) into role_result;

    select jsonb_build_object(
                   'account_id', get_account_billing_status.account_id,
                   'billing_subscription_id', s.id,
                   'billing_enabled', case
                                          when a.personal_account = true then config.enable_personal_account_billing
                                          else config.enable_team_account_billing end,
                   'billing_status', s.status,
                   'billing_customer_id', c.id,
                   'billing_provider', config.billing_provider,
                   'billing_email',
                   coalesce(c.email, u.email) -- if we don't have a customer email, use the user's email as a fallback
               )
    into result
    from basejump.accounts a
             join auth.users u on u.id = a.primary_owner_user_id
             left join basejump.billing_subscriptions s on s.account_id = a.id
             left join basejump.billing_customers c on c.account_id = coalesce(s.account_id, a.id)
             join basejump.config config on true
    where a.id = get_account_billing_status.account_id
    order by s.created desc
    limit 1;

    return result || role_result;
END;
$$;


ALTER FUNCTION "public"."get_account_billing_status"("account_id" "uuid") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_account_by_slug"("slug" "text") RETURNS "json"
    LANGUAGE "plpgsql"
    AS $$
DECLARE
    internal_account_id uuid;
BEGIN
    select a.id
    into internal_account_id
    from basejump.accounts a
    where a.slug IS NOT NULL
      and a.slug = get_account_by_slug.slug;

    return public.get_account(internal_account_id);
END;
$$;


ALTER FUNCTION "public"."get_account_by_slug"("slug" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_account_id"("slug" "text") RETURNS "uuid"
    LANGUAGE "sql"
    AS $$
select id
from basejump.accounts
where slug = get_account_id.slug;
$$;


ALTER FUNCTION "public"."get_account_id"("slug" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_account_invitations"("account_id" "uuid", "results_limit" integer DEFAULT 25, "results_offset" integer DEFAULT 0) RETURNS "json"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    -- only account owners can access this function
    if (select public.current_user_account_role(get_account_invitations.account_id) ->> 'account_role' <> 'owner') then
        raise exception 'Only account owners can access this function';
    end if;

    return (select json_agg(
                           json_build_object(
                                   'account_role', i.account_role,
                                   'created_at', i.created_at,
                                   'invitation_type', i.invitation_type,
                                   'invitation_id', i.id
                               )
                       )
            from basejump.invitations i
            where i.account_id = get_account_invitations.account_id
              and i.created_at > now() - interval '24 hours'
            limit coalesce(get_account_invitations.results_limit, 25) offset coalesce(get_account_invitations.results_offset, 0));
END;
$$;


ALTER FUNCTION "public"."get_account_invitations"("account_id" "uuid", "results_limit" integer, "results_offset" integer) OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_account_members"("account_id" "uuid", "results_limit" integer DEFAULT 50, "results_offset" integer DEFAULT 0) RETURNS "json"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'basejump'
    AS $$
BEGIN

    -- only account owners can access this function
    if (select public.current_user_account_role(get_account_members.account_id) ->> 'account_role' <> 'owner') then
        raise exception 'Only account owners can access this function';
    end if;

    return (select json_agg(
                           json_build_object(
                                   'user_id', wu.user_id,
                                   'account_role', wu.account_role,
                                   'name', p.name,
                                   'email', u.email,
                                   'is_primary_owner', a.primary_owner_user_id = wu.user_id
                               )
                       )
            from basejump.account_user wu
                     join basejump.accounts a on a.id = wu.account_id
                     join basejump.accounts p on p.primary_owner_user_id = wu.user_id and p.personal_account = true
                     join auth.users u on u.id = wu.user_id
            where wu.account_id = get_account_members.account_id
            limit coalesce(get_account_members.results_limit, 50) offset coalesce(get_account_members.results_offset, 0));
END;
$$;


ALTER FUNCTION "public"."get_account_members"("account_id" "uuid", "results_limit" integer, "results_offset" integer) OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_accounts"() RETURNS "json"
    LANGUAGE "sql"
    AS $$
select coalesce(json_agg(
                        json_build_object(
                                'account_id', wu.account_id,
                                'account_role', wu.account_role,
                                'is_primary_owner', a.primary_owner_user_id = auth.uid(),
                                'name', a.name,
                                'slug', a.slug,
                                'personal_account', a.personal_account,
                                'created_at', a.created_at,
                                'updated_at', a.updated_at
                            )
                    ), '[]'::json)
from basejump.account_user wu
         join basejump.accounts a on a.id = wu.account_id
where wu.user_id = auth.uid();
$$;


ALTER FUNCTION "public"."get_accounts"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_llm_formatted_messages"("p_thread_id" "uuid") RETURNS "jsonb"
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
DECLARE
    messages_array JSONB := '[]'::JSONB;
    has_access BOOLEAN;
    current_role TEXT;
    latest_summary_id UUID;
    latest_summary_time TIMESTAMP WITH TIME ZONE;
    is_project_public BOOLEAN;
BEGIN
    -- Get current role
    SELECT current_user INTO current_role;
    
    -- Check if associated project is public
    SELECT p.is_public INTO is_project_public
    FROM threads t
    LEFT JOIN projects p ON t.project_id = p.project_id
    WHERE t.thread_id = p_thread_id;
    
    -- Skip access check for service_role or public projects
    IF current_role = 'authenticated' AND NOT is_project_public THEN
        -- Check if thread exists and user has access
        SELECT EXISTS (
            SELECT 1 FROM threads t
            LEFT JOIN projects p ON t.project_id = p.project_id
            WHERE t.thread_id = p_thread_id
            AND (
                basejump.has_role_on_account(t.account_id) = true OR 
                basejump.has_role_on_account(p.account_id) = true
            )
        ) INTO has_access;
        
        IF NOT has_access THEN
            RAISE EXCEPTION 'Thread not found or access denied';
        END IF;
    END IF;

    -- Find the latest summary message if it exists
    SELECT message_id, created_at
    INTO latest_summary_id, latest_summary_time
    FROM messages
    WHERE thread_id = p_thread_id
    AND type = 'summary'
    AND is_llm_message = TRUE
    ORDER BY created_at DESC
    LIMIT 1;
    
    -- Log whether a summary was found (helpful for debugging)
    IF latest_summary_id IS NOT NULL THEN
        RAISE NOTICE 'Found latest summary message: id=%, time=%', latest_summary_id, latest_summary_time;
    ELSE
        RAISE NOTICE 'No summary message found for thread %', p_thread_id;
    END IF;

    -- Parse content if it's stored as a string and return proper JSON objects
    WITH parsed_messages AS (
        SELECT 
            message_id,
            CASE 
                WHEN jsonb_typeof(content) = 'string' THEN content::text::jsonb
                ELSE content
            END AS parsed_content,
            created_at,
            type
        FROM messages
        WHERE thread_id = p_thread_id
        AND is_llm_message = TRUE
        AND (
            -- Include the latest summary and all messages after it,
            -- or all messages if no summary exists
            latest_summary_id IS NULL 
            OR message_id = latest_summary_id 
            OR created_at > latest_summary_time
        )
        ORDER BY created_at
    )
    SELECT JSONB_AGG(parsed_content)
    INTO messages_array
    FROM parsed_messages;
    
    -- Handle the case when no messages are found
    IF messages_array IS NULL THEN
        RETURN '[]'::JSONB;
    END IF;
    
    RETURN messages_array;
END;
$$;


ALTER FUNCTION "public"."get_llm_formatted_messages"("p_thread_id" "uuid") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_marketplace_agents"("p_limit" integer DEFAULT 50, "p_offset" integer DEFAULT 0, "p_search" "text" DEFAULT NULL::"text", "p_tags" "text"[] DEFAULT NULL::"text"[]) RETURNS TABLE("agent_id" "uuid", "name" character varying, "description" "text", "system_prompt" "text", "configured_mcps" "jsonb", "agentpress_tools" "jsonb", "tags" "text"[], "download_count" integer, "marketplace_published_at" timestamp with time zone, "created_at" timestamp with time zone, "creator_name" "text", "avatar" "text", "avatar_color" "text")
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.agent_id,
        a.name,
        a.description,
        a.system_prompt,
        a.configured_mcps,
        a.agentpress_tools,
        a.tags,
        a.download_count,
        a.marketplace_published_at,
        a.created_at,
        COALESCE(acc.name, 'Anonymous')::TEXT as creator_name,
        a.avatar::TEXT,
        a.avatar_color::TEXT
    FROM agents a
    LEFT JOIN basejump.accounts acc ON a.account_id = acc.id
    WHERE a.is_public = true
    AND (p_search IS NULL OR 
         a.name ILIKE '%' || p_search || '%' OR 
         a.description ILIKE '%' || p_search || '%')
    AND (p_tags IS NULL OR a.tags && p_tags)
    ORDER BY a.marketplace_published_at DESC
    LIMIT p_limit
    OFFSET p_offset;
END;
$$;


ALTER FUNCTION "public"."get_marketplace_agents"("p_limit" integer, "p_offset" integer, "p_search" "text", "p_tags" "text"[]) OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."get_personal_account"() RETURNS "json"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    return public.get_account(auth.uid());
END;
$$;


ALTER FUNCTION "public"."get_personal_account"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."lookup_invitation"("lookup_invitation_token" "text") RETURNS "json"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public', 'basejump'
    AS $$
declare
    name              text;
    invitation_active boolean;
begin
    select account_name,
           case when id IS NOT NULL then true else false end as active
    into name, invitation_active
    from basejump.invitations
    where token = lookup_invitation_token
      and created_at > now() - interval '24 hours'
    limit 1;
    return json_build_object('active', coalesce(invitation_active, false), 'account_name', name);
end;
$$;


ALTER FUNCTION "public"."lookup_invitation"("lookup_invitation_token" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."publish_agent_to_marketplace"("p_agent_id" "uuid") RETURNS "void"
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM agents 
        WHERE agent_id = p_agent_id 
        AND basejump.has_role_on_account(account_id, 'owner')
    ) THEN
        RAISE EXCEPTION 'Agent not found or access denied';
    END IF;
    
    UPDATE agents 
    SET 
        is_public = true,
        marketplace_published_at = NOW()
    WHERE agent_id = p_agent_id;
END;
$$;


ALTER FUNCTION "public"."publish_agent_to_marketplace"("p_agent_id" "uuid") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."remove_account_member"("account_id" "uuid", "user_id" "uuid") RETURNS "void"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    -- only account owners can access this function
    if basejump.has_role_on_account(remove_account_member.account_id, 'owner') <> true then
        raise exception 'Only account owners can access this function';
    end if;

    delete
    from basejump.account_user wu
    where wu.account_id = remove_account_member.account_id
      and wu.user_id = remove_account_member.user_id;
END;
$$;


ALTER FUNCTION "public"."remove_account_member"("account_id" "uuid", "user_id" "uuid") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."service_role_upsert_customer_subscription"("account_id" "uuid", "customer" "jsonb" DEFAULT NULL::"jsonb", "subscription" "jsonb" DEFAULT NULL::"jsonb") RETURNS "void"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    -- if the customer is not null, upsert the data into billing_customers, only upsert fields that are present in the jsonb object
    if customer is not null then
        insert into basejump.billing_customers (id, account_id, email, provider)
        values (customer ->> 'id', service_role_upsert_customer_subscription.account_id, customer ->> 'billing_email',
                (customer ->> 'provider'))
        on conflict (id) do update
            set email = customer ->> 'billing_email';
    end if;

    -- if the subscription is not null, upsert the data into billing_subscriptions, only upsert fields that are present in the jsonb object
    if subscription is not null then
        insert into basejump.billing_subscriptions (id, account_id, billing_customer_id, status, metadata, price_id,
                                                    quantity, cancel_at_period_end, created, current_period_start,
                                                    current_period_end, ended_at, cancel_at, canceled_at, trial_start,
                                                    trial_end, plan_name, provider)
        values (subscription ->> 'id', service_role_upsert_customer_subscription.account_id,
                subscription ->> 'billing_customer_id', (subscription ->> 'status')::basejump.subscription_status,
                subscription -> 'metadata',
                subscription ->> 'price_id', (subscription ->> 'quantity')::int,
                (subscription ->> 'cancel_at_period_end')::boolean,
                (subscription ->> 'created')::timestamptz, (subscription ->> 'current_period_start')::timestamptz,
                (subscription ->> 'current_period_end')::timestamptz, (subscription ->> 'ended_at')::timestamptz,
                (subscription ->> 'cancel_at')::timestamptz,
                (subscription ->> 'canceled_at')::timestamptz, (subscription ->> 'trial_start')::timestamptz,
                (subscription ->> 'trial_end')::timestamptz,
                subscription ->> 'plan_name', (subscription ->> 'provider'))
        on conflict (id) do update
            set billing_customer_id  = subscription ->> 'billing_customer_id',
                status               = (subscription ->> 'status')::basejump.subscription_status,
                metadata             = subscription -> 'metadata',
                price_id             = subscription ->> 'price_id',
                quantity             = (subscription ->> 'quantity')::int,
                cancel_at_period_end = (subscription ->> 'cancel_at_period_end')::boolean,
                current_period_start = (subscription ->> 'current_period_start')::timestamptz,
                current_period_end   = (subscription ->> 'current_period_end')::timestamptz,
                ended_at             = (subscription ->> 'ended_at')::timestamptz,
                cancel_at            = (subscription ->> 'cancel_at')::timestamptz,
                canceled_at          = (subscription ->> 'canceled_at')::timestamptz,
                trial_start          = (subscription ->> 'trial_start')::timestamptz,
                trial_end            = (subscription ->> 'trial_end')::timestamptz,
                plan_name            = subscription ->> 'plan_name';
    end if;
end;
$$;


ALTER FUNCTION "public"."service_role_upsert_customer_subscription"("account_id" "uuid", "customer" "jsonb", "subscription" "jsonb") OWNER TO "postgres";

SET default_tablespace = '';

SET default_table_access_method = "heap";


CREATE TABLE IF NOT EXISTS "public"."devices" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "account_id" "uuid" NOT NULL,
    "name" "text",
    "last_seen" timestamp with time zone,
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "is_online" boolean DEFAULT false
);


ALTER TABLE "public"."devices" OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."transfer_device"("device_id" "uuid", "new_account_id" "uuid", "device_name" "text" DEFAULT NULL::"text") RETURNS SETOF "public"."devices"
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
DECLARE
  device_exists BOOLEAN;
  updated_device devices;
BEGIN
  -- Check if a device with the specified UUID exists
  SELECT EXISTS (
    SELECT 1 FROM devices WHERE id = device_id
  ) INTO device_exists;

  IF device_exists THEN
    -- Device exists: update its account ownership and last_seen timestamp
    UPDATE devices
    SET
      account_id = new_account_id, -- Update account_id instead of user_id
      name = COALESCE(device_name, name),
      last_seen = NOW()
    WHERE id = device_id
    RETURNING * INTO updated_device;

    RETURN NEXT updated_device;
  ELSE
    -- Device doesn't exist; return nothing so the caller can handle creation
    RETURN;
  END IF;
END;
$$;


ALTER FUNCTION "public"."transfer_device"("device_id" "uuid", "new_account_id" "uuid", "device_name" "text") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."unpublish_agent_from_marketplace"("p_agent_id" "uuid") RETURNS "void"
    LANGUAGE "plpgsql" SECURITY DEFINER
    AS $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM agents 
        WHERE agent_id = p_agent_id 
        AND basejump.has_role_on_account(account_id, 'owner')
    ) THEN
        RAISE EXCEPTION 'Agent not found or access denied';
    END IF;
    
    UPDATE agents 
    SET 
        is_public = false,
        marketplace_published_at = NULL
    WHERE agent_id = p_agent_id;
END;
$$;


ALTER FUNCTION "public"."unpublish_agent_from_marketplace"("p_agent_id" "uuid") OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."update_account"("account_id" "uuid", "slug" "text" DEFAULT NULL::"text", "name" "text" DEFAULT NULL::"text", "public_metadata" "jsonb" DEFAULT NULL::"jsonb", "replace_metadata" boolean DEFAULT false) RETURNS "json"
    LANGUAGE "plpgsql"
    AS $$
BEGIN

    -- check if postgres role is service_role
    if current_user IN ('anon', 'authenticated') and
       not (select current_user_account_role(update_account.account_id) ->> 'account_role' = 'owner') then
        raise exception 'Only account owners can update an account';
    end if;

    update basejump.accounts accounts
    set slug            = coalesce(update_account.slug, accounts.slug),
        name            = coalesce(update_account.name, accounts.name),
        public_metadata = case
                              when update_account.public_metadata is null then accounts.public_metadata -- do nothing
                              when accounts.public_metadata IS NULL then update_account.public_metadata -- set metadata
                              when update_account.replace_metadata
                                  then update_account.public_metadata -- replace metadata
                              else accounts.public_metadata || update_account.public_metadata end -- merge metadata
    where accounts.id = update_account.account_id;

    return public.get_account(account_id);
END;
$$;


ALTER FUNCTION "public"."update_account"("account_id" "uuid", "slug" "text", "name" "text", "public_metadata" "jsonb", "replace_metadata" boolean) OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."update_account_user_role"("account_id" "uuid", "user_id" "uuid", "new_account_role" "basejump"."account_role", "make_primary_owner" boolean DEFAULT false) RETURNS "void"
    LANGUAGE "plpgsql" SECURITY DEFINER
    SET "search_path" TO 'public'
    AS $$
declare
    is_account_owner         boolean;
    is_account_primary_owner boolean;
    changing_primary_owner   boolean;
begin
    -- check if the user is an owner, and if they are, allow them to update the role
    select basejump.has_role_on_account(update_account_user_role.account_id, 'owner') into is_account_owner;

    if not is_account_owner then
        raise exception 'You must be an owner of the account to update a users role';
    end if;

    -- check if the user being changed is the primary owner, if so its not allowed
    select primary_owner_user_id = auth.uid(), primary_owner_user_id = update_account_user_role.user_id
    into is_account_primary_owner, changing_primary_owner
    from basejump.accounts
    where id = update_account_user_role.account_id;

    if changing_primary_owner = true and is_account_primary_owner = false then
        raise exception 'You must be the primary owner of the account to change the primary owner';
    end if;

    update basejump.account_user au
    set account_role = new_account_role
    where au.account_id = update_account_user_role.account_id
      and au.user_id = update_account_user_role.user_id;

    if make_primary_owner = true then
        -- first we see if the current user is the owner, only they can do this
        if is_account_primary_owner = false then
            raise exception 'You must be the primary owner of the account to change the primary owner';
        end if;

        update basejump.accounts
        set primary_owner_user_id = update_account_user_role.user_id
        where id = update_account_user_role.account_id;
    end if;
end;
$$;


ALTER FUNCTION "public"."update_account_user_role"("account_id" "uuid", "user_id" "uuid", "new_account_role" "basejump"."account_role", "make_primary_owner" boolean) OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."update_agents_updated_at"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."update_agents_updated_at"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."update_updated_at_column"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc'::text, NOW());
    RETURN NEW;
END;
$$;


ALTER FUNCTION "public"."update_updated_at_column"() OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "basejump"."account_user" (
    "user_id" "uuid" NOT NULL,
    "account_id" "uuid" NOT NULL,
    "account_role" "basejump"."account_role" NOT NULL
);


ALTER TABLE "basejump"."account_user" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "basejump"."accounts" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "primary_owner_user_id" "uuid" DEFAULT "auth"."uid"() NOT NULL,
    "name" "text",
    "slug" "text",
    "personal_account" boolean DEFAULT false NOT NULL,
    "updated_at" timestamp with time zone,
    "created_at" timestamp with time zone,
    "created_by" "uuid",
    "updated_by" "uuid",
    "private_metadata" "jsonb" DEFAULT '{}'::"jsonb",
    "public_metadata" "jsonb" DEFAULT '{}'::"jsonb",
    CONSTRAINT "basejump_accounts_slug_null_if_personal_account_true" CHECK (((("personal_account" = true) AND ("slug" IS NULL)) OR (("personal_account" = false) AND ("slug" IS NOT NULL))))
);


ALTER TABLE "basejump"."accounts" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "basejump"."billing_customers" (
    "account_id" "uuid" NOT NULL,
    "id" "text" NOT NULL,
    "email" "text",
    "active" boolean,
    "provider" "text"
);


ALTER TABLE "basejump"."billing_customers" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "basejump"."billing_subscriptions" (
    "id" "text" NOT NULL,
    "account_id" "uuid" NOT NULL,
    "billing_customer_id" "text" NOT NULL,
    "status" "basejump"."subscription_status",
    "metadata" "jsonb",
    "price_id" "text",
    "plan_name" "text",
    "quantity" integer,
    "cancel_at_period_end" boolean,
    "created" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "current_period_start" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "current_period_end" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "ended_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()),
    "cancel_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()),
    "canceled_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()),
    "trial_start" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()),
    "trial_end" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()),
    "provider" "text"
);


ALTER TABLE "basejump"."billing_subscriptions" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "basejump"."config" (
    "enable_team_accounts" boolean DEFAULT true,
    "enable_personal_account_billing" boolean DEFAULT true,
    "enable_team_account_billing" boolean DEFAULT true,
    "billing_provider" "text" DEFAULT 'stripe'::"text"
);


ALTER TABLE "basejump"."config" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "basejump"."invitations" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "account_role" "basejump"."account_role" NOT NULL,
    "account_id" "uuid" NOT NULL,
    "token" "text" DEFAULT "basejump"."generate_token"(30) NOT NULL,
    "invited_by_user_id" "uuid" NOT NULL,
    "account_name" "text",
    "updated_at" timestamp with time zone,
    "created_at" timestamp with time zone,
    "invitation_type" "basejump"."invitation_type" NOT NULL
);


ALTER TABLE "basejump"."invitations" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."agent_runs" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "thread_id" "uuid" NOT NULL,
    "status" "text" DEFAULT 'running'::"text" NOT NULL,
    "started_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "completed_at" timestamp with time zone,
    "responses" "jsonb" DEFAULT '[]'::"jsonb" NOT NULL,
    "error" "text",
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL
);


ALTER TABLE "public"."agent_runs" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."agents" (
    "agent_id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "account_id" "uuid" NOT NULL,
    "name" character varying(255) NOT NULL,
    "description" "text",
    "system_prompt" "text" NOT NULL,
    "configured_mcps" "jsonb" DEFAULT '[]'::"jsonb",
    "agentpress_tools" "jsonb" DEFAULT '{}'::"jsonb",
    "is_default" boolean DEFAULT false,
    "avatar" character varying(10),
    "avatar_color" character varying(7),
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "is_public" boolean DEFAULT false,
    "marketplace_published_at" timestamp with time zone,
    "download_count" integer DEFAULT 0,
    "tags" "text"[] DEFAULT '{}'::"text"[]
);


ALTER TABLE "public"."agents" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."messages" (
    "message_id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "thread_id" "uuid" NOT NULL,
    "type" "text" NOT NULL,
    "is_llm_message" boolean DEFAULT true NOT NULL,
    "content" "jsonb" NOT NULL,
    "metadata" "jsonb" DEFAULT '{}'::"jsonb",
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL
);


ALTER TABLE "public"."messages" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."projects" (
    "project_id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "name" "text" NOT NULL,
    "description" "text",
    "account_id" "uuid" NOT NULL,
    "sandbox" "jsonb" DEFAULT '{}'::"jsonb",
    "is_public" boolean DEFAULT false,
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL
);


ALTER TABLE "public"."projects" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."recordings" (
    "id" "uuid" DEFAULT "extensions"."uuid_generate_v4"() NOT NULL,
    "account_id" "uuid" NOT NULL,
    "device_id" "uuid" NOT NULL,
    "preprocessed_file_path" "text",
    "meta" "jsonb",
    "created_at" timestamp with time zone DEFAULT "now"(),
    "updated_at" timestamp with time zone DEFAULT "now"(),
    "name" "text",
    "ui_annotated" boolean DEFAULT false,
    "a11y_file_path" "text",
    "audio_file_path" "text",
    "action_annotated" boolean DEFAULT false,
    "raw_data_file_path" "text",
    "metadata_file_path" "text",
    "action_training_file_path" "text"
);


ALTER TABLE "public"."recordings" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."threads" (
    "thread_id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "account_id" "uuid",
    "project_id" "uuid",
    "is_public" boolean DEFAULT false,
    "created_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "updated_at" timestamp with time zone DEFAULT "timezone"('utc'::"text", "now"()) NOT NULL,
    "agent_id" "uuid"
);


ALTER TABLE "public"."threads" OWNER TO "postgres";


COMMENT ON COLUMN "public"."threads"."agent_id" IS 'ID of the agent used for this conversation thread. If NULL, uses account default agent.';



CREATE TABLE IF NOT EXISTS "public"."user_agent_library" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "user_account_id" "uuid" NOT NULL,
    "original_agent_id" "uuid" NOT NULL,
    "agent_id" "uuid" NOT NULL,
    "added_at" timestamp with time zone DEFAULT "now"(),
    "is_favorite" boolean DEFAULT false
);


ALTER TABLE "public"."user_agent_library" OWNER TO "postgres";


ALTER TABLE ONLY "basejump"."account_user"
    ADD CONSTRAINT "account_user_pkey" PRIMARY KEY ("user_id", "account_id");



ALTER TABLE ONLY "basejump"."accounts"
    ADD CONSTRAINT "accounts_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "basejump"."accounts"
    ADD CONSTRAINT "accounts_slug_key" UNIQUE ("slug");



ALTER TABLE ONLY "basejump"."billing_customers"
    ADD CONSTRAINT "billing_customers_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "basejump"."billing_subscriptions"
    ADD CONSTRAINT "billing_subscriptions_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "basejump"."invitations"
    ADD CONSTRAINT "invitations_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "basejump"."invitations"
    ADD CONSTRAINT "invitations_token_key" UNIQUE ("token");



ALTER TABLE ONLY "public"."agent_runs"
    ADD CONSTRAINT "agent_runs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."agents"
    ADD CONSTRAINT "agents_pkey" PRIMARY KEY ("agent_id");



ALTER TABLE ONLY "public"."devices"
    ADD CONSTRAINT "devices_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."messages"
    ADD CONSTRAINT "messages_pkey" PRIMARY KEY ("message_id");



ALTER TABLE ONLY "public"."projects"
    ADD CONSTRAINT "projects_pkey" PRIMARY KEY ("project_id");



ALTER TABLE ONLY "public"."recordings"
    ADD CONSTRAINT "recordings_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."threads"
    ADD CONSTRAINT "threads_pkey" PRIMARY KEY ("thread_id");



ALTER TABLE ONLY "public"."user_agent_library"
    ADD CONSTRAINT "user_agent_library_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."user_agent_library"
    ADD CONSTRAINT "user_agent_library_user_account_id_original_agent_id_key" UNIQUE ("user_account_id", "original_agent_id");



CREATE INDEX "idx_agent_runs_created_at" ON "public"."agent_runs" USING "btree" ("created_at");



CREATE INDEX "idx_agent_runs_status" ON "public"."agent_runs" USING "btree" ("status");



CREATE INDEX "idx_agent_runs_thread_id" ON "public"."agent_runs" USING "btree" ("thread_id");



CREATE UNIQUE INDEX "idx_agents_account_default" ON "public"."agents" USING "btree" ("account_id", "is_default") WHERE ("is_default" = true);



CREATE INDEX "idx_agents_account_id" ON "public"."agents" USING "btree" ("account_id");



CREATE INDEX "idx_agents_created_at" ON "public"."agents" USING "btree" ("created_at");



CREATE INDEX "idx_agents_download_count" ON "public"."agents" USING "btree" ("download_count");



CREATE INDEX "idx_agents_is_default" ON "public"."agents" USING "btree" ("is_default");



CREATE INDEX "idx_agents_is_public" ON "public"."agents" USING "btree" ("is_public");



CREATE INDEX "idx_agents_marketplace_published_at" ON "public"."agents" USING "btree" ("marketplace_published_at");



CREATE INDEX "idx_agents_tags" ON "public"."agents" USING "gin" ("tags");



CREATE INDEX "idx_devices_account_id" ON "public"."devices" USING "btree" ("account_id");



CREATE INDEX "idx_messages_created_at" ON "public"."messages" USING "btree" ("created_at");



CREATE INDEX "idx_messages_thread_id" ON "public"."messages" USING "btree" ("thread_id");



CREATE INDEX "idx_projects_account_id" ON "public"."projects" USING "btree" ("account_id");



CREATE INDEX "idx_projects_created_at" ON "public"."projects" USING "btree" ("created_at");



CREATE INDEX "idx_recordings_account_id" ON "public"."recordings" USING "btree" ("account_id");



CREATE INDEX "idx_recordings_device_id" ON "public"."recordings" USING "btree" ("device_id");



CREATE INDEX "idx_threads_account_id" ON "public"."threads" USING "btree" ("account_id");



CREATE INDEX "idx_threads_agent_id" ON "public"."threads" USING "btree" ("agent_id");



CREATE INDEX "idx_threads_created_at" ON "public"."threads" USING "btree" ("created_at");



CREATE INDEX "idx_threads_project_id" ON "public"."threads" USING "btree" ("project_id");



CREATE INDEX "idx_user_agent_library_added_at" ON "public"."user_agent_library" USING "btree" ("added_at");



CREATE INDEX "idx_user_agent_library_agent_id" ON "public"."user_agent_library" USING "btree" ("agent_id");



CREATE INDEX "idx_user_agent_library_original_agent" ON "public"."user_agent_library" USING "btree" ("original_agent_id");



CREATE INDEX "idx_user_agent_library_user_account" ON "public"."user_agent_library" USING "btree" ("user_account_id");



CREATE OR REPLACE TRIGGER "basejump_add_current_user_to_new_account" AFTER INSERT ON "basejump"."accounts" FOR EACH ROW EXECUTE FUNCTION "basejump"."add_current_user_to_new_account"();



CREATE OR REPLACE TRIGGER "basejump_protect_account_fields" BEFORE UPDATE ON "basejump"."accounts" FOR EACH ROW EXECUTE FUNCTION "basejump"."protect_account_fields"();



CREATE OR REPLACE TRIGGER "basejump_set_accounts_timestamp" BEFORE INSERT OR UPDATE ON "basejump"."accounts" FOR EACH ROW EXECUTE FUNCTION "basejump"."trigger_set_timestamps"();



CREATE OR REPLACE TRIGGER "basejump_set_accounts_user_tracking" BEFORE INSERT OR UPDATE ON "basejump"."accounts" FOR EACH ROW EXECUTE FUNCTION "basejump"."trigger_set_user_tracking"();



CREATE OR REPLACE TRIGGER "basejump_set_invitations_timestamp" BEFORE INSERT OR UPDATE ON "basejump"."invitations" FOR EACH ROW EXECUTE FUNCTION "basejump"."trigger_set_timestamps"();



CREATE OR REPLACE TRIGGER "basejump_slugify_account_slug" BEFORE INSERT OR UPDATE ON "basejump"."accounts" FOR EACH ROW EXECUTE FUNCTION "basejump"."slugify_account_slug"();



CREATE OR REPLACE TRIGGER "basejump_trigger_set_invitation_details" BEFORE INSERT ON "basejump"."invitations" FOR EACH ROW EXECUTE FUNCTION "basejump"."trigger_set_invitation_details"();



CREATE OR REPLACE TRIGGER "trigger_agents_updated_at" BEFORE UPDATE ON "public"."agents" FOR EACH ROW EXECUTE FUNCTION "public"."update_agents_updated_at"();



CREATE OR REPLACE TRIGGER "update_agent_runs_updated_at" BEFORE UPDATE ON "public"."agent_runs" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



CREATE OR REPLACE TRIGGER "update_messages_updated_at" BEFORE UPDATE ON "public"."messages" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



CREATE OR REPLACE TRIGGER "update_projects_updated_at" BEFORE UPDATE ON "public"."projects" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



CREATE OR REPLACE TRIGGER "update_threads_updated_at" BEFORE UPDATE ON "public"."threads" FOR EACH ROW EXECUTE FUNCTION "public"."update_updated_at_column"();



ALTER TABLE ONLY "basejump"."account_user"
    ADD CONSTRAINT "account_user_account_id_fkey" FOREIGN KEY ("account_id") REFERENCES "basejump"."accounts"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "basejump"."account_user"
    ADD CONSTRAINT "account_user_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "auth"."users"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "basejump"."accounts"
    ADD CONSTRAINT "accounts_created_by_fkey" FOREIGN KEY ("created_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "basejump"."accounts"
    ADD CONSTRAINT "accounts_primary_owner_user_id_fkey" FOREIGN KEY ("primary_owner_user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "basejump"."accounts"
    ADD CONSTRAINT "accounts_updated_by_fkey" FOREIGN KEY ("updated_by") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "basejump"."billing_customers"
    ADD CONSTRAINT "billing_customers_account_id_fkey" FOREIGN KEY ("account_id") REFERENCES "basejump"."accounts"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "basejump"."billing_subscriptions"
    ADD CONSTRAINT "billing_subscriptions_account_id_fkey" FOREIGN KEY ("account_id") REFERENCES "basejump"."accounts"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "basejump"."billing_subscriptions"
    ADD CONSTRAINT "billing_subscriptions_billing_customer_id_fkey" FOREIGN KEY ("billing_customer_id") REFERENCES "basejump"."billing_customers"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "basejump"."invitations"
    ADD CONSTRAINT "invitations_account_id_fkey" FOREIGN KEY ("account_id") REFERENCES "basejump"."accounts"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "basejump"."invitations"
    ADD CONSTRAINT "invitations_invited_by_user_id_fkey" FOREIGN KEY ("invited_by_user_id") REFERENCES "auth"."users"("id");



ALTER TABLE ONLY "public"."agent_runs"
    ADD CONSTRAINT "agent_runs_thread_id_fkey" FOREIGN KEY ("thread_id") REFERENCES "public"."threads"("thread_id");



ALTER TABLE ONLY "public"."agents"
    ADD CONSTRAINT "agents_account_id_fkey" FOREIGN KEY ("account_id") REFERENCES "basejump"."accounts"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."devices"
    ADD CONSTRAINT "fk_account" FOREIGN KEY ("account_id") REFERENCES "basejump"."accounts"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."recordings"
    ADD CONSTRAINT "fk_account" FOREIGN KEY ("account_id") REFERENCES "basejump"."accounts"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."recordings"
    ADD CONSTRAINT "fk_device" FOREIGN KEY ("device_id") REFERENCES "public"."devices"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."messages"
    ADD CONSTRAINT "messages_thread_id_fkey" FOREIGN KEY ("thread_id") REFERENCES "public"."threads"("thread_id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."projects"
    ADD CONSTRAINT "projects_account_id_fkey" FOREIGN KEY ("account_id") REFERENCES "basejump"."accounts"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."threads"
    ADD CONSTRAINT "threads_account_id_fkey" FOREIGN KEY ("account_id") REFERENCES "basejump"."accounts"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."threads"
    ADD CONSTRAINT "threads_agent_id_fkey" FOREIGN KEY ("agent_id") REFERENCES "public"."agents"("agent_id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."threads"
    ADD CONSTRAINT "threads_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "public"."projects"("project_id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."user_agent_library"
    ADD CONSTRAINT "user_agent_library_agent_id_fkey" FOREIGN KEY ("agent_id") REFERENCES "public"."agents"("agent_id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."user_agent_library"
    ADD CONSTRAINT "user_agent_library_original_agent_id_fkey" FOREIGN KEY ("original_agent_id") REFERENCES "public"."agents"("agent_id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."user_agent_library"
    ADD CONSTRAINT "user_agent_library_user_account_id_fkey" FOREIGN KEY ("user_account_id") REFERENCES "basejump"."accounts"("id") ON DELETE CASCADE;



CREATE POLICY "Account users can be deleted by owners except primary account o" ON "basejump"."account_user" FOR DELETE TO "authenticated" USING ((("basejump"."has_role_on_account"("account_id", 'owner'::"basejump"."account_role") = true) AND ("user_id" <> ( SELECT "accounts"."primary_owner_user_id"
   FROM "basejump"."accounts"
  WHERE ("account_user"."account_id" = "accounts"."id")))));



CREATE POLICY "Accounts are viewable by members" ON "basejump"."accounts" FOR SELECT TO "authenticated" USING (("basejump"."has_role_on_account"("id") = true));



CREATE POLICY "Accounts are viewable by primary owner" ON "basejump"."accounts" FOR SELECT TO "authenticated" USING (("primary_owner_user_id" = "auth"."uid"()));



CREATE POLICY "Accounts can be edited by owners" ON "basejump"."accounts" FOR UPDATE TO "authenticated" USING (("basejump"."has_role_on_account"("id", 'owner'::"basejump"."account_role") = true));



CREATE POLICY "Basejump settings can be read by authenticated users" ON "basejump"."config" FOR SELECT TO "authenticated" USING (true);



CREATE POLICY "Can only view own billing customer data." ON "basejump"."billing_customers" FOR SELECT USING (("basejump"."has_role_on_account"("account_id") = true));



CREATE POLICY "Can only view own billing subscription data." ON "basejump"."billing_subscriptions" FOR SELECT USING (("basejump"."has_role_on_account"("account_id") = true));



CREATE POLICY "Invitations can be created by account owners" ON "basejump"."invitations" FOR INSERT TO "authenticated" WITH CHECK ((("basejump"."is_set"('enable_team_accounts'::"text") = true) AND (( SELECT "accounts"."personal_account"
   FROM "basejump"."accounts"
  WHERE ("accounts"."id" = "invitations"."account_id")) = false) AND ("basejump"."has_role_on_account"("account_id", 'owner'::"basejump"."account_role") = true)));



CREATE POLICY "Invitations can be deleted by account owners" ON "basejump"."invitations" FOR DELETE TO "authenticated" USING (("basejump"."has_role_on_account"("account_id", 'owner'::"basejump"."account_role") = true));



CREATE POLICY "Invitations viewable by account owners" ON "basejump"."invitations" FOR SELECT TO "authenticated" USING ((("created_at" > ("now"() - '24:00:00'::interval)) AND ("basejump"."has_role_on_account"("account_id", 'owner'::"basejump"."account_role") = true)));



CREATE POLICY "Team accounts can be created by any user" ON "basejump"."accounts" FOR INSERT TO "authenticated" WITH CHECK ((("basejump"."is_set"('enable_team_accounts'::"text") = true) AND ("personal_account" = false)));



ALTER TABLE "basejump"."account_user" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "basejump"."accounts" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "basejump"."billing_customers" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "basejump"."billing_subscriptions" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "basejump"."config" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "basejump"."invitations" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "users can view their own account_users" ON "basejump"."account_user" FOR SELECT TO "authenticated" USING (("user_id" = "auth"."uid"()));



CREATE POLICY "users can view their teammates" ON "basejump"."account_user" FOR SELECT TO "authenticated" USING (("basejump"."has_role_on_account"("account_id") = true));



CREATE POLICY "Account members can delete their own devices" ON "public"."devices" FOR DELETE USING ("basejump"."has_role_on_account"("account_id"));



CREATE POLICY "Account members can delete their own recordings" ON "public"."recordings" FOR DELETE USING ("basejump"."has_role_on_account"("account_id"));



CREATE POLICY "Account members can insert their own devices" ON "public"."devices" FOR INSERT WITH CHECK ("basejump"."has_role_on_account"("account_id"));



CREATE POLICY "Account members can insert their own recordings" ON "public"."recordings" FOR INSERT WITH CHECK ("basejump"."has_role_on_account"("account_id"));



CREATE POLICY "Account members can only access their own devices" ON "public"."devices" USING ("basejump"."has_role_on_account"("account_id"));



CREATE POLICY "Account members can only access their own recordings" ON "public"."recordings" USING ("basejump"."has_role_on_account"("account_id"));



CREATE POLICY "Account members can update their own devices" ON "public"."devices" FOR UPDATE USING ("basejump"."has_role_on_account"("account_id"));



CREATE POLICY "Account members can update their own recordings" ON "public"."recordings" FOR UPDATE USING ("basejump"."has_role_on_account"("account_id"));



CREATE POLICY "Account members can view their own devices" ON "public"."devices" FOR SELECT USING ("basejump"."has_role_on_account"("account_id"));



CREATE POLICY "Account members can view their own recordings" ON "public"."recordings" FOR SELECT USING ("basejump"."has_role_on_account"("account_id"));



CREATE POLICY "agent_run_delete_policy" ON "public"."agent_runs" FOR DELETE USING ((EXISTS ( SELECT 1
   FROM ("public"."threads"
     LEFT JOIN "public"."projects" ON (("threads"."project_id" = "projects"."project_id")))
  WHERE (("threads"."thread_id" = "agent_runs"."thread_id") AND (("basejump"."has_role_on_account"("threads"."account_id") = true) OR ("basejump"."has_role_on_account"("projects"."account_id") = true))))));



CREATE POLICY "agent_run_insert_policy" ON "public"."agent_runs" FOR INSERT WITH CHECK ((EXISTS ( SELECT 1
   FROM ("public"."threads"
     LEFT JOIN "public"."projects" ON (("threads"."project_id" = "projects"."project_id")))
  WHERE (("threads"."thread_id" = "agent_runs"."thread_id") AND (("basejump"."has_role_on_account"("threads"."account_id") = true) OR ("basejump"."has_role_on_account"("projects"."account_id") = true))))));



CREATE POLICY "agent_run_select_policy" ON "public"."agent_runs" FOR SELECT USING ((EXISTS ( SELECT 1
   FROM ("public"."threads"
     LEFT JOIN "public"."projects" ON (("threads"."project_id" = "projects"."project_id")))
  WHERE (("threads"."thread_id" = "agent_runs"."thread_id") AND (("projects"."is_public" = true) OR ("basejump"."has_role_on_account"("threads"."account_id") = true) OR ("basejump"."has_role_on_account"("projects"."account_id") = true))))));



CREATE POLICY "agent_run_update_policy" ON "public"."agent_runs" FOR UPDATE USING ((EXISTS ( SELECT 1
   FROM ("public"."threads"
     LEFT JOIN "public"."projects" ON (("threads"."project_id" = "projects"."project_id")))
  WHERE (("threads"."thread_id" = "agent_runs"."thread_id") AND (("basejump"."has_role_on_account"("threads"."account_id") = true) OR ("basejump"."has_role_on_account"("projects"."account_id") = true))))));



ALTER TABLE "public"."agent_runs" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."agents" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "agents_delete_own" ON "public"."agents" FOR DELETE USING (("basejump"."has_role_on_account"("account_id", 'owner'::"basejump"."account_role") AND ("is_default" = false)));



CREATE POLICY "agents_insert_own" ON "public"."agents" FOR INSERT WITH CHECK ("basejump"."has_role_on_account"("account_id", 'owner'::"basejump"."account_role"));



CREATE POLICY "agents_select_marketplace" ON "public"."agents" FOR SELECT USING ((("is_public" = true) OR "basejump"."has_role_on_account"("account_id")));



CREATE POLICY "agents_select_own" ON "public"."agents" FOR SELECT USING ("basejump"."has_role_on_account"("account_id"));



CREATE POLICY "agents_update_own" ON "public"."agents" FOR UPDATE USING ("basejump"."has_role_on_account"("account_id", 'owner'::"basejump"."account_role"));



ALTER TABLE "public"."devices" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "message_delete_policy" ON "public"."messages" FOR DELETE USING ((EXISTS ( SELECT 1
   FROM ("public"."threads"
     LEFT JOIN "public"."projects" ON (("threads"."project_id" = "projects"."project_id")))
  WHERE (("threads"."thread_id" = "messages"."thread_id") AND (("basejump"."has_role_on_account"("threads"."account_id") = true) OR ("basejump"."has_role_on_account"("projects"."account_id") = true))))));



CREATE POLICY "message_insert_policy" ON "public"."messages" FOR INSERT WITH CHECK ((EXISTS ( SELECT 1
   FROM ("public"."threads"
     LEFT JOIN "public"."projects" ON (("threads"."project_id" = "projects"."project_id")))
  WHERE (("threads"."thread_id" = "messages"."thread_id") AND (("basejump"."has_role_on_account"("threads"."account_id") = true) OR ("basejump"."has_role_on_account"("projects"."account_id") = true))))));



CREATE POLICY "message_select_policy" ON "public"."messages" FOR SELECT USING ((EXISTS ( SELECT 1
   FROM ("public"."threads"
     LEFT JOIN "public"."projects" ON (("threads"."project_id" = "projects"."project_id")))
  WHERE (("threads"."thread_id" = "messages"."thread_id") AND (("projects"."is_public" = true) OR ("basejump"."has_role_on_account"("threads"."account_id") = true) OR ("basejump"."has_role_on_account"("projects"."account_id") = true))))));



CREATE POLICY "message_update_policy" ON "public"."messages" FOR UPDATE USING ((EXISTS ( SELECT 1
   FROM ("public"."threads"
     LEFT JOIN "public"."projects" ON (("threads"."project_id" = "projects"."project_id")))
  WHERE (("threads"."thread_id" = "messages"."thread_id") AND (("basejump"."has_role_on_account"("threads"."account_id") = true) OR ("basejump"."has_role_on_account"("projects"."account_id") = true))))));



ALTER TABLE "public"."messages" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "project_delete_policy" ON "public"."projects" FOR DELETE USING (("basejump"."has_role_on_account"("account_id") = true));



CREATE POLICY "project_insert_policy" ON "public"."projects" FOR INSERT WITH CHECK (("basejump"."has_role_on_account"("account_id") = true));



CREATE POLICY "project_select_policy" ON "public"."projects" FOR SELECT USING ((("is_public" = true) OR ("basejump"."has_role_on_account"("account_id") = true)));



CREATE POLICY "project_update_policy" ON "public"."projects" FOR UPDATE USING (("basejump"."has_role_on_account"("account_id") = true));



ALTER TABLE "public"."projects" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."recordings" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "thread_delete_policy" ON "public"."threads" FOR DELETE USING ((("basejump"."has_role_on_account"("account_id") = true) OR (EXISTS ( SELECT 1
   FROM "public"."projects"
  WHERE (("projects"."project_id" = "threads"."project_id") AND ("basejump"."has_role_on_account"("projects"."account_id") = true))))));



CREATE POLICY "thread_insert_policy" ON "public"."threads" FOR INSERT WITH CHECK ((("basejump"."has_role_on_account"("account_id") = true) OR (EXISTS ( SELECT 1
   FROM "public"."projects"
  WHERE (("projects"."project_id" = "threads"."project_id") AND ("basejump"."has_role_on_account"("projects"."account_id") = true))))));



CREATE POLICY "thread_select_policy" ON "public"."threads" FOR SELECT USING ((("is_public" IS TRUE) OR ("basejump"."has_role_on_account"("account_id") = true) OR (EXISTS ( SELECT 1
   FROM "public"."projects"
  WHERE (("projects"."project_id" = "threads"."project_id") AND (("projects"."is_public" IS TRUE) OR ("basejump"."has_role_on_account"("projects"."account_id") = true)))))));



CREATE POLICY "thread_update_policy" ON "public"."threads" FOR UPDATE USING ((("basejump"."has_role_on_account"("account_id") = true) OR (EXISTS ( SELECT 1
   FROM "public"."projects"
  WHERE (("projects"."project_id" = "threads"."project_id") AND ("basejump"."has_role_on_account"("projects"."account_id") = true))))));



ALTER TABLE "public"."threads" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."user_agent_library" ENABLE ROW LEVEL SECURITY;


CREATE POLICY "user_agent_library_delete_own" ON "public"."user_agent_library" FOR DELETE USING ("basejump"."has_role_on_account"("user_account_id"));



CREATE POLICY "user_agent_library_insert_own" ON "public"."user_agent_library" FOR INSERT WITH CHECK ("basejump"."has_role_on_account"("user_account_id"));



CREATE POLICY "user_agent_library_select_own" ON "public"."user_agent_library" FOR SELECT USING ("basejump"."has_role_on_account"("user_account_id"));



CREATE POLICY "user_agent_library_update_own" ON "public"."user_agent_library" FOR UPDATE USING ("basejump"."has_role_on_account"("user_account_id"));





ALTER PUBLICATION "supabase_realtime" OWNER TO "postgres";


GRANT USAGE ON SCHEMA "basejump" TO "authenticated";
GRANT USAGE ON SCHEMA "basejump" TO "service_role";



GRANT USAGE ON SCHEMA "public" TO "postgres";
GRANT USAGE ON SCHEMA "public" TO "anon";
GRANT USAGE ON SCHEMA "public" TO "authenticated";
GRANT USAGE ON SCHEMA "public" TO "service_role";



REVOKE ALL ON FUNCTION "basejump"."add_current_user_to_new_account"() FROM PUBLIC;



REVOKE ALL ON FUNCTION "basejump"."generate_token"("length" integer) FROM PUBLIC;
GRANT ALL ON FUNCTION "basejump"."generate_token"("length" integer) TO "authenticated";



REVOKE ALL ON FUNCTION "basejump"."get_accounts_with_role"("passed_in_role" "basejump"."account_role") FROM PUBLIC;
GRANT ALL ON FUNCTION "basejump"."get_accounts_with_role"("passed_in_role" "basejump"."account_role") TO "authenticated";



REVOKE ALL ON FUNCTION "basejump"."get_config"() FROM PUBLIC;
GRANT ALL ON FUNCTION "basejump"."get_config"() TO "authenticated";
GRANT ALL ON FUNCTION "basejump"."get_config"() TO "service_role";



GRANT ALL ON FUNCTION "basejump"."has_role_on_account"("account_id" "uuid", "account_role" "basejump"."account_role") TO "authenticated";
GRANT ALL ON FUNCTION "basejump"."has_role_on_account"("account_id" "uuid", "account_role" "basejump"."account_role") TO "anon";
GRANT ALL ON FUNCTION "basejump"."has_role_on_account"("account_id" "uuid", "account_role" "basejump"."account_role") TO "service_role";



REVOKE ALL ON FUNCTION "basejump"."is_set"("field_name" "text") FROM PUBLIC;
GRANT ALL ON FUNCTION "basejump"."is_set"("field_name" "text") TO "authenticated";



REVOKE ALL ON FUNCTION "basejump"."protect_account_fields"() FROM PUBLIC;



REVOKE ALL ON FUNCTION "basejump"."run_new_user_setup"() FROM PUBLIC;



REVOKE ALL ON FUNCTION "basejump"."slugify_account_slug"() FROM PUBLIC;



REVOKE ALL ON FUNCTION "basejump"."trigger_set_invitation_details"() FROM PUBLIC;



REVOKE ALL ON FUNCTION "basejump"."trigger_set_timestamps"() FROM PUBLIC;



REVOKE ALL ON FUNCTION "basejump"."trigger_set_user_tracking"() FROM PUBLIC;











































































































































































REVOKE ALL ON FUNCTION "public"."accept_invitation"("lookup_invitation_token" "text") FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."accept_invitation"("lookup_invitation_token" "text") TO "service_role";
GRANT ALL ON FUNCTION "public"."accept_invitation"("lookup_invitation_token" "text") TO "authenticated";



REVOKE ALL ON FUNCTION "public"."add_agent_to_library"("p_original_agent_id" "uuid", "p_user_account_id" "uuid") FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."add_agent_to_library"("p_original_agent_id" "uuid", "p_user_account_id" "uuid") TO "service_role";
GRANT ALL ON FUNCTION "public"."add_agent_to_library"("p_original_agent_id" "uuid", "p_user_account_id" "uuid") TO "authenticated";



REVOKE ALL ON FUNCTION "public"."create_account"("slug" "text", "name" "text") FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."create_account"("slug" "text", "name" "text") TO "service_role";
GRANT ALL ON FUNCTION "public"."create_account"("slug" "text", "name" "text") TO "authenticated";



REVOKE ALL ON FUNCTION "public"."create_invitation"("account_id" "uuid", "account_role" "basejump"."account_role", "invitation_type" "basejump"."invitation_type") FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."create_invitation"("account_id" "uuid", "account_role" "basejump"."account_role", "invitation_type" "basejump"."invitation_type") TO "service_role";
GRANT ALL ON FUNCTION "public"."create_invitation"("account_id" "uuid", "account_role" "basejump"."account_role", "invitation_type" "basejump"."invitation_type") TO "authenticated";



REVOKE ALL ON FUNCTION "public"."current_user_account_role"("account_id" "uuid") FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."current_user_account_role"("account_id" "uuid") TO "service_role";
GRANT ALL ON FUNCTION "public"."current_user_account_role"("account_id" "uuid") TO "authenticated";



REVOKE ALL ON FUNCTION "public"."delete_invitation"("invitation_id" "uuid") FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."delete_invitation"("invitation_id" "uuid") TO "service_role";
GRANT ALL ON FUNCTION "public"."delete_invitation"("invitation_id" "uuid") TO "authenticated";



REVOKE ALL ON FUNCTION "public"."get_account"("account_id" "uuid") FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."get_account"("account_id" "uuid") TO "service_role";
GRANT ALL ON FUNCTION "public"."get_account"("account_id" "uuid") TO "authenticated";



REVOKE ALL ON FUNCTION "public"."get_account_billing_status"("account_id" "uuid") FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."get_account_billing_status"("account_id" "uuid") TO "service_role";
GRANT ALL ON FUNCTION "public"."get_account_billing_status"("account_id" "uuid") TO "authenticated";



REVOKE ALL ON FUNCTION "public"."get_account_by_slug"("slug" "text") FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."get_account_by_slug"("slug" "text") TO "service_role";
GRANT ALL ON FUNCTION "public"."get_account_by_slug"("slug" "text") TO "authenticated";



REVOKE ALL ON FUNCTION "public"."get_account_id"("slug" "text") FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."get_account_id"("slug" "text") TO "service_role";
GRANT ALL ON FUNCTION "public"."get_account_id"("slug" "text") TO "authenticated";



REVOKE ALL ON FUNCTION "public"."get_account_invitations"("account_id" "uuid", "results_limit" integer, "results_offset" integer) FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."get_account_invitations"("account_id" "uuid", "results_limit" integer, "results_offset" integer) TO "service_role";
GRANT ALL ON FUNCTION "public"."get_account_invitations"("account_id" "uuid", "results_limit" integer, "results_offset" integer) TO "authenticated";



REVOKE ALL ON FUNCTION "public"."get_account_members"("account_id" "uuid", "results_limit" integer, "results_offset" integer) FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."get_account_members"("account_id" "uuid", "results_limit" integer, "results_offset" integer) TO "service_role";
GRANT ALL ON FUNCTION "public"."get_account_members"("account_id" "uuid", "results_limit" integer, "results_offset" integer) TO "authenticated";



REVOKE ALL ON FUNCTION "public"."get_accounts"() FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."get_accounts"() TO "service_role";
GRANT ALL ON FUNCTION "public"."get_accounts"() TO "authenticated";



REVOKE ALL ON FUNCTION "public"."get_llm_formatted_messages"("p_thread_id" "uuid") FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."get_llm_formatted_messages"("p_thread_id" "uuid") TO "service_role";
GRANT ALL ON FUNCTION "public"."get_llm_formatted_messages"("p_thread_id" "uuid") TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_llm_formatted_messages"("p_thread_id" "uuid") TO "anon";



REVOKE ALL ON FUNCTION "public"."get_marketplace_agents"("p_limit" integer, "p_offset" integer, "p_search" "text", "p_tags" "text"[]) FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."get_marketplace_agents"("p_limit" integer, "p_offset" integer, "p_search" "text", "p_tags" "text"[]) TO "service_role";
GRANT ALL ON FUNCTION "public"."get_marketplace_agents"("p_limit" integer, "p_offset" integer, "p_search" "text", "p_tags" "text"[]) TO "authenticated";
GRANT ALL ON FUNCTION "public"."get_marketplace_agents"("p_limit" integer, "p_offset" integer, "p_search" "text", "p_tags" "text"[]) TO "anon";



REVOKE ALL ON FUNCTION "public"."get_personal_account"() FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."get_personal_account"() TO "service_role";
GRANT ALL ON FUNCTION "public"."get_personal_account"() TO "authenticated";



REVOKE ALL ON FUNCTION "public"."lookup_invitation"("lookup_invitation_token" "text") FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."lookup_invitation"("lookup_invitation_token" "text") TO "service_role";
GRANT ALL ON FUNCTION "public"."lookup_invitation"("lookup_invitation_token" "text") TO "authenticated";



REVOKE ALL ON FUNCTION "public"."publish_agent_to_marketplace"("p_agent_id" "uuid") FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."publish_agent_to_marketplace"("p_agent_id" "uuid") TO "service_role";
GRANT ALL ON FUNCTION "public"."publish_agent_to_marketplace"("p_agent_id" "uuid") TO "authenticated";



REVOKE ALL ON FUNCTION "public"."remove_account_member"("account_id" "uuid", "user_id" "uuid") FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."remove_account_member"("account_id" "uuid", "user_id" "uuid") TO "service_role";
GRANT ALL ON FUNCTION "public"."remove_account_member"("account_id" "uuid", "user_id" "uuid") TO "authenticated";



REVOKE ALL ON FUNCTION "public"."service_role_upsert_customer_subscription"("account_id" "uuid", "customer" "jsonb", "subscription" "jsonb") FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."service_role_upsert_customer_subscription"("account_id" "uuid", "customer" "jsonb", "subscription" "jsonb") TO "service_role";



GRANT ALL ON TABLE "public"."devices" TO "anon";
GRANT ALL ON TABLE "public"."devices" TO "authenticated";
GRANT ALL ON TABLE "public"."devices" TO "service_role";



REVOKE ALL ON FUNCTION "public"."transfer_device"("device_id" "uuid", "new_account_id" "uuid", "device_name" "text") FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."transfer_device"("device_id" "uuid", "new_account_id" "uuid", "device_name" "text") TO "service_role";
GRANT ALL ON FUNCTION "public"."transfer_device"("device_id" "uuid", "new_account_id" "uuid", "device_name" "text") TO "authenticated";



REVOKE ALL ON FUNCTION "public"."unpublish_agent_from_marketplace"("p_agent_id" "uuid") FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."unpublish_agent_from_marketplace"("p_agent_id" "uuid") TO "service_role";
GRANT ALL ON FUNCTION "public"."unpublish_agent_from_marketplace"("p_agent_id" "uuid") TO "authenticated";



REVOKE ALL ON FUNCTION "public"."update_account"("account_id" "uuid", "slug" "text", "name" "text", "public_metadata" "jsonb", "replace_metadata" boolean) FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."update_account"("account_id" "uuid", "slug" "text", "name" "text", "public_metadata" "jsonb", "replace_metadata" boolean) TO "service_role";
GRANT ALL ON FUNCTION "public"."update_account"("account_id" "uuid", "slug" "text", "name" "text", "public_metadata" "jsonb", "replace_metadata" boolean) TO "authenticated";



REVOKE ALL ON FUNCTION "public"."update_account_user_role"("account_id" "uuid", "user_id" "uuid", "new_account_role" "basejump"."account_role", "make_primary_owner" boolean) FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."update_account_user_role"("account_id" "uuid", "user_id" "uuid", "new_account_role" "basejump"."account_role", "make_primary_owner" boolean) TO "service_role";
GRANT ALL ON FUNCTION "public"."update_account_user_role"("account_id" "uuid", "user_id" "uuid", "new_account_role" "basejump"."account_role", "make_primary_owner" boolean) TO "authenticated";



REVOKE ALL ON FUNCTION "public"."update_agents_updated_at"() FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."update_agents_updated_at"() TO "service_role";



REVOKE ALL ON FUNCTION "public"."update_updated_at_column"() FROM PUBLIC;
GRANT ALL ON FUNCTION "public"."update_updated_at_column"() TO "service_role";












GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE "basejump"."account_user" TO "authenticated";
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE "basejump"."account_user" TO "service_role";



GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE "basejump"."accounts" TO "authenticated";
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE "basejump"."accounts" TO "service_role";



GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE "basejump"."billing_customers" TO "service_role";
GRANT SELECT ON TABLE "basejump"."billing_customers" TO "authenticated";



GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE "basejump"."billing_subscriptions" TO "service_role";
GRANT SELECT ON TABLE "basejump"."billing_subscriptions" TO "authenticated";



GRANT SELECT ON TABLE "basejump"."config" TO "authenticated";
GRANT SELECT ON TABLE "basejump"."config" TO "service_role";



GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE "basejump"."invitations" TO "authenticated";
GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE "basejump"."invitations" TO "service_role";









GRANT ALL ON TABLE "public"."agent_runs" TO "anon";
GRANT ALL ON TABLE "public"."agent_runs" TO "authenticated";
GRANT ALL ON TABLE "public"."agent_runs" TO "service_role";



GRANT ALL ON TABLE "public"."agents" TO "anon";
GRANT ALL ON TABLE "public"."agents" TO "authenticated";
GRANT ALL ON TABLE "public"."agents" TO "service_role";



GRANT ALL ON TABLE "public"."messages" TO "anon";
GRANT ALL ON TABLE "public"."messages" TO "authenticated";
GRANT ALL ON TABLE "public"."messages" TO "service_role";



GRANT ALL ON TABLE "public"."projects" TO "anon";
GRANT ALL ON TABLE "public"."projects" TO "authenticated";
GRANT ALL ON TABLE "public"."projects" TO "service_role";



GRANT ALL ON TABLE "public"."recordings" TO "anon";
GRANT ALL ON TABLE "public"."recordings" TO "authenticated";
GRANT ALL ON TABLE "public"."recordings" TO "service_role";



GRANT ALL ON TABLE "public"."threads" TO "anon";
GRANT ALL ON TABLE "public"."threads" TO "authenticated";
GRANT ALL ON TABLE "public"."threads" TO "service_role";



GRANT ALL ON TABLE "public"."user_agent_library" TO "anon";
GRANT ALL ON TABLE "public"."user_agent_library" TO "authenticated";
GRANT ALL ON TABLE "public"."user_agent_library" TO "service_role";









ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES  TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS  TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "anon";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "authenticated";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES  TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" REVOKE ALL ON FUNCTIONS  FROM PUBLIC;



























RESET ALL;
