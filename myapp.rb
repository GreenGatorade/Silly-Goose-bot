require 'sinatra'
require 'json'

set :port, (ENV['PORT'] || 4567).to_i
set :bind, '0.0.0.0'
set :protection, except: :host_authorization

# Create messages.json if it doesn't exist yet
File.write('messages.json', '[]') unless File.exist?('messages.json')

get '/' do
  @messages = JSON.parse(File.read('messages.json')) rescue []
  erb :index
end
