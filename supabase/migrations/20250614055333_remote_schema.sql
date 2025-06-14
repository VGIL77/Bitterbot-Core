create policy "Allow specific users to delete profiles"
on "public"."profiles"
as permissive
for delete
to public
using ((auth.uid() = ANY (ARRAY['ea16f8ab-2bd5-4939-8a9a-5842d94ed380'::uuid, '3ba994c3-5a1e-409e-84aa-e53c77964de8'::uuid, '6e8f8ae7-7b5d-4c6e-a3da-afa7536210ce'::uuid])));


create policy "Allow specific users to insert profiles"
on "public"."profiles"
as permissive
for insert
to public
with check ((auth.uid() = ANY (ARRAY['ea16f8ab-2bd5-4939-8a9a-5842d94ed380'::uuid, '3ba994c3-5a1e-409e-84aa-e53c77964de8'::uuid, '6e8f8ae7-7b5d-4c6e-a3da-afa7536210ce'::uuid])));


create policy "Allow specific users to select profiles"
on "public"."profiles"
as permissive
for select
to public
using ((auth.uid() = ANY (ARRAY['ea16f8ab-2bd5-4939-8a9a-5842d94ed380'::uuid, '3ba994c3-5a1e-409e-84aa-e53c77964de8'::uuid, '6e8f8ae7-7b5d-4c6e-a3da-afa7536210ce'::uuid])));


create policy "Allow specific users to update profiles"
on "public"."profiles"
as permissive
for update
to public
using ((auth.uid() = ANY (ARRAY['ea16f8ab-2bd5-4939-8a9a-5842d94ed380'::uuid, '3ba994c3-5a1e-409e-84aa-e53c77964de8'::uuid, '6e8f8ae7-7b5d-4c6e-a3da-afa7536210ce'::uuid])));



