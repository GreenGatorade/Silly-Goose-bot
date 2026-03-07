FROM ruby:3.4.6

# Install Python
RUN apt-get update && apt-get install -y python3 python3-pip && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Ruby gems
COPY Gemfile Gemfile.lock ./
RUN bundle install

# Install Python packages
COPY requirements.txt ./
RUN pip3 install -r requirements.txt --break-system-packages

# Copy app
COPY . .

# Create messages.json if missing
RUN [ -f messages.json ] || echo '[]' > messages.json

EXPOSE 8080

CMD python3 bot.py & ruby myapp.rb
