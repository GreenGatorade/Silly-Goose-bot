require 'sinatra/activerecord'
require 'sqlite3'

ActiveRecord::Base.establish_connection(
  adapter: 'sqlite3',
  database: 'mydatabase.db'
)

require_relative 'migration_program'

ActiveRecord::MigrationContext.new(
  'db/migrate',
  ActiveRecord::SchemaMigration
).up
