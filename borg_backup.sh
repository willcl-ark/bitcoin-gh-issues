#!/bin/sh

# Check for BORG_REPO
if [ -z "$BORG_REPO" ]; then
  echo "BORG_REPO environment variable not found. Please set it before proceeding."
  exit 1
fi

# Check for BORG_PASSPHRASE
if [ -z "$BORG_PASSPHRASE" ]; then
  echo "BORG_PASSPHRASE environment variable not found. Please set it before proceeding."
  exit 1
fi

# some helpers and error handling:
info() { printf "\n%s %s\n\n" "$(date)" "$*" >&2; }
trap 'echo $( date ) Backup interrupted >&2; exit 2' INT TERM

info "Starting backup"

# Backup the most important directories into an archive named after
# the machine this script is currently running on:

borg create \
	--verbose \
	--filter AME \
	--list \
	--stats \
	--show-rc \
	--compression lz4 \
	--exclude-caches \
	\
	::'{hostname}-{now}' \
	/home/ubuntu/bitcoin-github/issues.db

backup_exit=$?

info "Pruning repository"

# Use the `prune` subcommand to maintain 7 daily, 4 weekly and 6 monthly
# archives of THIS machine. The '{hostname}-*' matching is very important to
# limit prune's operation to this machine's archives and not apply to
# other machines' archives also:

borg prune \
	--list \
	--glob-archives '{hostname}-*' \
	--show-rc \
	--keep-minutely 10 \
	--keep-hourly 6 \
	--keep-daily 7 \
	--keep-weekly 4 \
	--keep-monthly 6

prune_exit=$?

# actually free repo disk space by compacting segments

info "Compacting repository"

borg compact

compact_exit=$?

# use highest exit code as global exit code
global_exit=$((backup_exit > prune_exit ? backup_exit : prune_exit))
global_exit=$((compact_exit > global_exit ? compact_exit : global_exit))

if [ ${global_exit} -eq 0 ]; then
	info "Backup, Prune, and Compact finished successfully"
elif [ ${global_exit} -eq 1 ]; then
	info "Backup, Prune, and/or Compact finished with warnings"
else
	info "Backup, Prune, and/or Compact finished with errors"
fi

exit ${global_exit}
