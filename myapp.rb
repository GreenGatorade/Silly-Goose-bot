require 'sinatra'
require 'json'
set :port, ENV['PORT'] || 4567

get '/' do
  @messages = JSON.parse(File.read('messages.json')) rescue []
  erb :index
end
