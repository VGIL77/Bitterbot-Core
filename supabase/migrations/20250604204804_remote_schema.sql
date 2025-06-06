CREATE TRIGGER on_auth_user_created AFTER INSERT ON auth.users FOR EACH ROW EXECUTE FUNCTION basejump.run_new_user_setup();


create policy "Account members can delete recording files"
on "storage"."objects"
as permissive
for delete
to authenticated
using (((bucket_id = 'recordings'::text) AND (((storage.foldername(name))[1])::uuid IN ( SELECT basejump.get_accounts_with_role() AS get_accounts_with_role))));


create policy "Account members can insert recording files"
on "storage"."objects"
as permissive
for insert
to authenticated
with check (((bucket_id = 'recordings'::text) AND (((storage.foldername(name))[1])::uuid IN ( SELECT basejump.get_accounts_with_role() AS get_accounts_with_role))));


create policy "Account members can select recording files"
on "storage"."objects"
as permissive
for select
to authenticated
using (((bucket_id = 'recordings'::text) AND (((storage.foldername(name))[1])::uuid IN ( SELECT basejump.get_accounts_with_role() AS get_accounts_with_role))));


create policy "Account members can update recording files"
on "storage"."objects"
as permissive
for update
to authenticated
using (((bucket_id = 'recordings'::text) AND (((storage.foldername(name))[1])::uuid IN ( SELECT basejump.get_accounts_with_role() AS get_accounts_with_role))));



