# Security Policy

The security and privacy of SondeAlert users are important to us.

If you believe you have discovered a security vulnerability, please report it privately and responsibly.

**Do not publish security vulnerabilities through a public GitHub Issue.**

---

## Supported versions

SondeAlert is currently distributed through a closed Google Play testing programme.

| Version | Supported |
|---|---|
| Latest Google Play test release | Yes |
| Older test releases | No |
| Builds obtained outside Google Play | No |

Testers should always update to the latest available Google Play test release before reporting a problem.

Security fixes will normally be included in a new Google Play test release.

---

## Reporting a security vulnerability

Use one of the following private reporting methods:

1. Use GitHub’s **Private vulnerability reporting** option in the Security section of this repository, if available.
2. Contact the developer through the private communication channel used by the SondeAlert testing group.

Clearly mark your message as:

**SondeAlert security report**

Do not include vulnerability details in a public GitHub Issue, Discussion or social-media message.

---

## Information to include

A useful security report should contain:

- A clear description of the vulnerability
- The affected SondeAlert version
- Device manufacturer and model
- Android version
- Steps required to reproduce the problem
- The expected result
- The actual result
- Screenshots, logs or a screen recording where appropriate
- An explanation of the possible security or privacy impact
- Whether the issue can be reproduced consistently

Include only the information necessary to investigate the problem.

Do not include:

- Passwords
- Authentication tokens
- Private API keys
- Your exact home address
- Personal data belonging to another person
- Complete device backups
- Unrelated application data

If a log contains exact GPS coordinates or other personal information, remove or obscure that information before submitting it unless it is essential to reproduce the vulnerability.

---

## What qualifies as a security vulnerability?

Examples include:

- Unauthorised access to locally stored application data
- Exposure of precise location information without the user’s knowledge
- A way to bypass Android permissions
- Execution of unintended commands or code
- Manipulation of downloaded data that creates a security risk
- Unsafe handling of external links or intents
- Exposure of secrets, credentials or private developer information
- A vulnerability in the update or release process
- A reproducible crash that can be deliberately triggered to cause a security impact

A normal application crash, incorrect radiosonde position or user-interface problem is generally considered a regular bug unless it also creates a security or privacy risk.

Regular bugs can be reported through the normal testing channel or GitHub Issues.

---

## Responsible testing

When investigating a possible vulnerability:

- Test only on devices and accounts you own or are authorised to use
- Do not attempt to access another person’s data
- Do not interfere with other users
- Do not perform denial-of-service or high-volume API testing
- Do not attempt to disrupt Radiosondy.info, map providers or other external services
- Do not use social engineering
- Do not publicly disclose the vulnerability before it has been investigated
- Stop testing if it could cause data loss, service disruption or personal risk

Testing SondeAlert does not grant permission to test third-party systems.

Vulnerabilities affecting Radiosondy.info, MapLibre, OpenStreetMap services, Google Play or Android itself should be reported to the responsible organisation.

---

## What happens after a report?

After receiving a valid security report, we will aim to:

1. Confirm that the report has been received.
2. Review the supplied information.
3. Attempt to reproduce the vulnerability.
4. Determine its severity and affected versions.
5. Prepare and test a fix where necessary.
6. Distribute the fix through Google Play.
7. Inform the reporter when the issue has been resolved or when more information is required.

SondeAlert is an independently developed project, so response and resolution times may vary depending on the complexity of the issue.

Please allow a reasonable amount of time for investigation before requesting an update.

---

## Coordinated disclosure

Please keep vulnerability details private until:

- A corrected version has been made available;
- Affected testers have had a reasonable opportunity to update; and
- Public disclosure has been agreed with the developer.

Where appropriate, reporters can be credited for responsibly reporting a vulnerability. A reporter may also choose to remain anonymous.

---

## Application distribution

Official SondeAlert Android releases are distributed through Google Play.

Installing APK files from unofficial or unknown sources may bypass protections provided by Google Play and is not supported.

Before reporting unexpected behaviour, verify that:

- SondeAlert was installed through the official testing link;
- Google Play shows the latest available version; and
- The application package has not been modified.

---

## Third-party services

SondeAlert uses or interacts with third-party services and projects, including:

- Radiosondy.info
- MapLibre
- OpenStreetMap-based map services
- Google Play services
- Android system services

The SondeAlert developer cannot directly correct vulnerabilities in third-party systems.

However, if a third-party issue is caused or exposed by the way SondeAlert uses a service, it can still be reported privately so the application-side risk can be investigated.

---

## Public repository

This repository contains public documentation, screenshots and community information.

The production application source code and release signing information are maintained separately and are not published in this repository.

Never submit signing keys, passwords, tokens or private configuration files to this repository.

---

Thank you for helping keep SondeAlert and its users safe.
