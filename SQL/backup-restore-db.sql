use wallet

declare @backup_path VARCHAR(max)
declare @backup_name VARCHAR(max)
declare @backup_disk VARCHAR(max)
set @backup_path = 'D:\My Documents\Informatica\Python\WALL€T\Wallet\backup\'
set @backup_name = 'Wallet_' + convert(varchar, getdate(), 5) + '.bak'
set @backup_disk = @backup_path + @backup_name
print @backup_path + @backup_name
backup database wallet
to disk = @backup_disk

-- TODO TERMINARE
-- restore database wallet   
-- from disk = @backup_path
-- with replace

