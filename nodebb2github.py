import requests
import json
import time
from markdownify import markdownify as md
from datetime import datetime
import sys
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Nodebb base URL of the forum (e.g. "https://forum.site.com")
from_nodebb_base_url = "https://forum.site.com"
# Nodebb forum category identifier to migrate (e.g "2")
from_nodebb_category = "2"
# Skip migration of topics until the specified one (e.g. "46/user-input-processing")
from_nodebb_skip_until_topic = None

# GitHub personal token
github_token = "XXXXXXXX"
# GitHub repository with Discussions enabled to migrate into (e.g. "username/repository")
to_github_repository = "username/repository"
# GitHub Discussion category to migrate into (e.g. "General")
to_github_category = "General"
# GitHub path where Nodebb uploads files have been copied ("master/files") 
to_github_uploads = "master/files"
# Run but do not migrate the content
dry_run = False
# version of this script
version = "1.0"

### 

# GraphQL for retrieving the repositoryId
get_repository_id = """
{
  viewer {
    repositories(first: 100, affiliations: [OWNER, ORGANIZATION_MEMBER, COLLABORATOR], ownerAffiliations: [OWNER, ORGANIZATION_MEMBER, COLLABORATOR]) {
      totalCount
      nodes {
        nameWithOwner
        id
      }
    }
  }
}
"""
# GraphQL for retrieving the categoryId
get_categories_id = """
query categories ($owner: String!, $name: String!){
  repository(owner: $owner, name: $name) {
   discussionCategories(last:10){
        edges{
          node {
            id
            name
          }
     }
  }
  }
}
"""
# GraphQL for creating a discussion
create_discussion = """
mutation ($repositoryId: ID!, $categoryId: ID!, $body: String!, $title: String!){
  createDiscussion(input: {
     repositoryId: $repositoryId, 
     categoryId: $categoryId, 
     body: $body,
     title: $title
  }) {
    discussion {
      title
      url
      id
    }
  }
}
"""

# GraphQL for adding a comment to a discussion
add_comment = """
mutation ($discussionId: ID!, $body: String!){
  addDiscussionComment(input: {
     discussionId: $discussionId,
     body: $body
  }) {
    comment {
      id
    }
  }
}
"""

# Run a GraphQL API call
def run_query(query, variables): # A simple function to use requests.post to make the API call. Note the json= section.
    if dry_run: return {}
    headers = {"Authorization": "Bearer "+github_token}
    request = requests.post('https://api.github.com/graphql', json={'query': query, 'variables': variables}, headers=headers, verify=False)
    if request.status_code == 200:
        return request.json()
    else:
        print("Query failed to run by returning code of {}. {}".format(request.status_code, query))
        sys.exit()

# migrate a topic from a Nodebb URL
def migrate_topic(url):
  print("Migrating post "+url)
  request = requests.get(url, verify=False)
  if request.status_code != 200:
      print(request.json())
      sys.exit() 
  a = request.json()
  title = md(a["title"])
  discussionId = None
  for p in a["posts"]:
    body = md(p["content"].replace("\\n","").replace("\n",""))
    user = p["user"]["username"]
    date = datetime.fromtimestamp(int(p["timestamp"]/1000))
    body = "[*This post has been migrated from the old forum, it was originally sent by* **"+str(user)+"** *on* **"+str(date)+"**]\n\n"+body
    body = body.replace("/assets/uploads/files","https://raw.githubusercontent.com/"+to_github_repository+"/"+to_github_uploads)
    if discussionId is None:
      result = run_query(create_discussion, {'repositoryId' : repositoryId,'categoryId' : categoryId, 'title':title,'body':body})
      if "errors" in result:
        print(result["errors"][0]["message"])
        sys.exit()
      #print(json.dumps(result, indent=4))
      try: 
        discussionId = result["data"]["createDiscussion"]["discussion"]["id"]
      except:
        if not dry_run: sys.exit()
    else:
      result = run_query(add_comment, {'discussionId' : discussionId,'body':body})
      #print(json.dumps(result, indent=4))
      if "errors" in result:
        print(result["errors"][0]["message"])
        sys.exit()
    time.sleep(1)
        
# migrate all the topics belonging to a Nodebb category identifier
def migrate_topics(category):
  request = requests.get(from_nodebb_base_url+"/api/category/"+category, verify=False)
  if request.status_code == 200:
    a = request.json()
    a["topics"].reverse()
    to_migrate = False if from_nodebb_skip_until_topic is not None else True
    for p in a["topics"]:
      if p["deleted"] == 1: 
        continue
      if from_nodebb_skip_until_topic is not None and p["slug"] == from_nodebb_skip_until_topic: 
        to_migrate = True
      url = from_nodebb_base_url+"/api/topic/"+str(p["slug"])
      if to_migrate: 
        migrate_topic(url)

## MAIN ##
repositoryId = None
categoryId = None

print("Nodebb2GitHub v"+version)
# load custom configuration file if any
try: 
  from config import *
except:
  pass
# ask the user if willing to proceed
print("Press any key to migrate Nodebb Forum at URL "+from_nodebb_base_url+", category '"+from_nodebb_category+"', into GitHub Discussions "+to_github_repository+", category "+to_github_category+". CTRL+C to abort")
input()

# Get the Github repositoryId
result = run_query(get_repository_id,None)
if "errors" in result:
  print(result["errors"][0]["message"])
  sys.exit()
for p in result["data"]["viewer"]["repositories"]["nodes"]:
  if p["nameWithOwner"] == to_github_repository:
    repositoryId = p["id"]
    break
if repositoryId is None:
  print("Unable to retrieve repositoryId")
  sys.exit()

# Get the Github categoryId
split = to_github_repository.split("/")
result = run_query(get_categories_id,{'owner': split[0],'name': split[1]})
if "errors" in result:
  print(result["errors"][0]["message"])
  sys.exit()
for p in result["data"]["repository"]["discussionCategories"]["edges"]:
  if p["node"]["name"] == to_github_category:
    categoryId = p["node"]["id"]
    break
if categoryId is None:
  print("Unable to retrieve categoryId")
  sys.exit()

# migrate all the topics of the given nodebb category to github discussions
migrate_topics(from_nodebb_category)