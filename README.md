# Nodebb2GitHub

The script migrates a Nodebb Forum to GitHub Discussions.
Given a Nodebb category identifier, the script retrieves all the posts belonging to that category by calling Nodebb API and migrates all of them into a previously setup GitHub Discussions location (by using GraphQL API).

## Requirements
* A Github personal access token (https://docs.github.com/en/enterprise-server@3.4/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
* A GitHub repository with Discussions enabled
* Nodebb forum with infinite scrolling disabled and a value set to "Posts per Pages" and "Topics per Pages" enough to show all the topics/posts in a single page (https://forum.site.com/admin/settings/pagination)

## Configuration

Edit the variables on top of the script (or create a file called `config.py` in the same directory of the script) before running it:
* `from_nodebb_base_url`: Nodebb base URL of the forum (e.g. "https://forum.site.com")
* `from_nodebb_category`: Nodebb forum category identifier to migrate (e.g "2")
* `from_nodebb_skip_until_topic`: Skip migration of topics until the specified one (e.g. "46/user-input-processing")
* `github_token`: GitHub personal token
* `to_github_repository`: GitHub repository with Discussions enabled to migrate into (e.g. "username/repository")
* `to_github_category`: GitHub Discussion category to migrate into (e.g. "General")
* `to_github_uploads`: GitHub path where Nodebb uploads files have been copied ("master/files") 

## Limitations

Due to GitHub APIs' limitations, the script cannot migrate the original timestamp and author of the posts.