import nextcord
from nextcord.ext import commands
import logging
from dotenv import load_dotenv
import os

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')

# Configure logging
logging.basicConfig(filename='discord_bot_log.log', level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')


intents = nextcord.Intents.default()
intents.messages = True
intents.guilds = True
intents.members = True
intents.message_content = True  # Add this line


bot = commands.Bot(command_prefix='!', intents=intents)

# Global variables
custom_mention = "@custom"
admin_mod_roles = []
custom_names = []
common_names = ["Admin", "Moderator", "Administrator", "Mod", "help"]  # Add more as needed

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    logging.info("Bot started.")

@bot.slash_command(name="setcustommention", description="Set a custom mention")
async def set_custom_mention(interaction: nextcord.Interaction, new_mention: str):
    global custom_mention
    custom_mention = new_mention
    await interaction.response.send_message(f"Custom mention set to: {custom_mention}")
    logging.info(f"Custom mention changed to: {custom_mention}")

@bot.slash_command(name="setadminmodroles", description="Set admin and moderator roles")
async def set_admin_mod_roles(interaction: nextcord.Interaction, roles: str):
    global admin_mod_roles
    admin_mod_roles = roles.split(", ")
    await interaction.response.send_message(f"Admin/Mod roles set to: {', '.join(admin_mod_roles)}")
    logging.info(f"Admin/Mod roles changed to: {', '.join(admin_mod_roles)}")

@bot.slash_command(name="setcustomnames", description="Set custom names for checks")
async def set_custom_names(interaction: nextcord.Interaction, names: str):
    global custom_names
    custom_names = names.split(", ")
    await interaction.response.send_message(f"Custom names set to: {', '.join(custom_names)}")
    logging.info(f"Custom names changed to: {', '.join(custom_names)}")

async def perform_check_perms(guild):
    logging.info("Checking permissions...")

    # Accumulate data for roles
    roles_with_high_permissions = []
    for role in guild.roles:
        if role.permissions.administrator or role.permissions.manage_roles or role.permissions.manage_guild:
            roles_with_high_permissions.append(role.name)
            logging.info(f"PERMISSION ISSUE: Role '{role.name}' ({role.id}) has high-level permissions.")

    # Accumulate data for members with high permissions
    members_with_high_permissions = {}
    for member in guild.members:
        member_roles = [role.name for role in member.roles if role.name in roles_with_high_permissions]
        if member_roles:
            members_with_high_permissions[member.display_name] = member_roles
            logging.info(f"PERMISSION ISSUE: Member '{member.display_name}' (ID: {member.id}) has high-level permissions through roles: {', '.join(member_roles)}")

    return roles_with_high_permissions, members_with_high_permissions




async def perform_check_channels(guild):
    logging.info("Checking which roles can mention @everyone, @here, and @custom in channels...")
    channel_permissions_data = {}

    for channel in guild.text_channels:
        for role in guild.roles:
            # Skip @everyone role for individual permission check
            if role.is_default():
                continue

            # Check if the role can mention @everyone (which includes @here)
            can_mention_everyone = channel.permissions_for(role).mention_everyone
            can_send_messages = channel.permissions_for(role).send_messages

            if can_mention_everyone:
                message = f"CHANNEL MENTION ISSUE: Role '{role.name}' ({role.id}) can mention @everyone/@here in {channel.name} ({channel.id})."
                channel_permissions_data.setdefault(channel.name, []).append(message)
                logging.info(message)

            if can_send_messages:
                message = f"CHANNEL MENTION ISSUE: Role '{role.name}' ({role.id}) can send messages (and possibly use @custom) in {channel.name} ({channel.id})."
                channel_permissions_data.setdefault(channel.name, []).append(message)
                logging.info(message)

    # Log the data in a structured format
    for channel, data in channel_permissions_data.items():
        logging.info(f"Channel: {channel}")
        for item in data:
            logging.info(f"  - {item}")

    return channel_permissions_data




async def perform_check_names(guild):
    logging.info("Checking member names...")
    all_names_to_check = set(admin_mod_roles + common_names + custom_names)
    member_matches = {}

    for member in guild.members:
        matches = []

        # Check if any role of the member matches the names to check
        role_matches = [role.name for role in member.roles if role.name in all_names_to_check]
        if role_matches:
            matches.append(f"Role Matches: {', '.join(role_matches)}")
            # Include specific keyword for summary tracking
            logging.info(f"NAME ISSUE: Member '{member.display_name}' (ID: {member.id}) has roles matching sensitive names.")

        # Additionally, check if the member's display name matches any of the names to check
        if any(name.lower() in member.display_name.lower() for name in all_names_to_check):
            matches.append("Display Name Match")
            # Include specific keyword for summary tracking
            logging.info(f"NAME ISSUE: Member '{member.display_name}' (ID: {member.id}) display name matches sensitive names.")

        if matches:
            member_matches[member.display_name] = matches

    # Log the findings in a structured format
    for member_name, matches in member_matches.items():
        logging.info(f"Member: {member_name}")
        for match in matches:
            logging.info(f"  - {match}")

    return member_matches







# ... [previous code remains unchanged]

async def perform_check_manage_permissions(guild):
    logging.info("Checking manage channels, webhooks, and roles permissions...")
    role_permissions_data = {}

    for member in guild.members:
        for role in member.roles:
            if role.permissions.manage_channels or role.permissions.manage_webhooks or role.permissions.manage_roles:
                if role.name not in role_permissions_data:
                    role_permissions_data[role.name] = []
                # Include a specific keyword for summary tracking
                log_message = f"WEBHOOK AND OTHER: Member '{member.display_name}' ({member.id}) can manage channels/webhooks/roles through '{role.name}' ({role.id})."
                role_permissions_data[role.name].append(log_message)
                logging.info(log_message)

    # Structured logging for each role
    for role, data in role_permissions_data.items():
        logging.info(f"Role: {role}")
        for item in data:
            logging.info(f"  - {item}")

    return role_permissions_data



# Function to check for permission to create private threads
async def perform_check_private_threads(guild):
    logging.info("Checking private thread creation permissions...")
    role_permissions_data = {}

    for member in guild.members:
        for role in member.roles:
            if role.permissions.create_private_threads:
                if role.name not in role_permissions_data:
                    role_permissions_data[role.name] = []
                # Include a specific keyword in the log statement
                log_message = f"PRIVATE THREAD ISSUE: Member '{member.display_name}' ({member.id}) can create private threads through '{role.name}' ({role.id})."
                role_permissions_data[role.name].append(log_message)
                logging.info(log_message)
                break  # Break to avoid duplicate entries if member has multiple roles with these permissions

    # Structured logging for each role
    for role, data in role_permissions_data.items():
        logging.info(f"Role: {role}")
        for item in data:
            logging.info(f"  - {item}")

    return role_permissions_data



    

@bot.slash_command(
    name="runsecuritychecks",
    description="Run all security checks",
    default_member_permissions=nextcord.Permissions(administrator=True)
)
async def run_security_checks(interaction: nextcord.Interaction):
    await interaction.response.defer()
    if interaction.guild is None:
        await interaction.followup.send("This command can only be used in a guild.")
        return
    
    await interaction.followup.send("🔍 Starting security checks...")

    await perform_check_perms(interaction.guild)
    await interaction.followup.send("✅ Permissions check completed.")

    await perform_check_channels(interaction.guild)
    await interaction.followup.send("✅ Channel mentions check completed.")

    await perform_check_names(interaction.guild)
    await interaction.followup.send("✅ Member names check completed.")

    await perform_check_manage_permissions(interaction.guild)
    await interaction.followup.send("✅ Manage channels/webhooks/roles permissions check completed.")

    await perform_check_private_threads(interaction.guild)
    await interaction.followup.send("✅ Private thread creation permissions check completed.")


    await interaction.followup.send("🔍 All security checks completed.")



@bot.slash_command(
    name="generatereport",
    description="Generate a report from logs",
    default_member_permissions=nextcord.Permissions(administrator=True)
)
async def generate_report(interaction: nextcord.Interaction):
    await interaction.response.defer()
    log_file_path = 'discord_bot_log.log'

    # Calculate summary of issues
    issue_summary = {
        "PERMISSION ISSUE": 0,
        "CHANNEL MENTION ISSUE": 0,
        "NAME ISSUE": 0,
        "PRIVATE THREAD ISSUE": 0,
        "WEBHOOK AND OTHER": 0
        # Add more categories as per your logging
    }

    full_report = ""
    with open(log_file_path, 'r') as file:
        for line in file:
            full_report += line
            for issue_type in issue_summary:
                if issue_type in line:
                    issue_summary[issue_type] += 1

    summary_message = "Summary of Issues:\n" + "\n".join(f"{key}: {value}" for key, value in issue_summary.items())

    # Send the summary and the full report directly to the user who invoked the command
    try:
        # Send the summary
        await interaction.user.send(content=summary_message)

        # If the full report is too long, consider sending it as a file
        if len(full_report) < 2000:
            await interaction.user.send(content=f"Full Report:\n{full_report}")
        else:
            with open(log_file_path, 'rb') as file:
                await interaction.user.send(content="Full Report:", file=nextcord.File(file, 'full_report.txt'))

        await interaction.followup.send("The summary and the full report have been sent to your DM.")
    except Exception as e:
        await interaction.followup.send(f"Error sending DM: {e}. Please ensure your DMs are open.")

    # Clear the log file
    with open(log_file_path, 'w') as file:
        file.truncate()




bot.run(DISCORD_TOKEN)
