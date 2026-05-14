from datetime import timedelta

from django.core.files.base import ContentFile
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from tournaments.models import (
    JuryRegistrationStatus,
    JuryTournamentRegistration,
    Team,
    TeamMember,
    Tournament,
    TournamentFile,
    User,
    UserRole,
)


def make_user(email, nickname, role):
    return User.objects.create_user(
        email=email,
        password='Test1234!',
        nickname=nickname,
        role=role,
        is_verified=True,
    )


def make_tournament():
    now = timezone.now()
    return Tournament.objects.create(
        title='Files Cup',
        description='Files access tournament',
        reg_start=now - timedelta(days=5),
        reg_end=now - timedelta(days=3),
        start_time=now - timedelta(days=2),
        end_time=now + timedelta(days=2),
    )


class TournamentFilesAccessTests(APITestCase):
    def setUp(self):
        self.tournament = make_tournament()
        self.admin = make_user('admin-files@test.com', 'admin_files', UserRole.ADMIN)
        self.organizer = make_user('organizer-files@test.com', 'organizer_files', UserRole.ORGANIZER)
        self.jury = make_user('jury-files@test.com', 'jury_files', UserRole.JURY)
        self.participant = make_user('participant-files@test.com', 'participant_files', UserRole.PARTICIPANT)
        self.outsider = make_user('outsider-files@test.com', 'outsider_files', UserRole.PARTICIPANT)

        self.team = Team.objects.create(
            name='Files Team',
            tournament=self.tournament,
            captain=self.participant,
            captain_email=self.participant.email,
            captain_name='Files Captain',
        )
        TeamMember.objects.create(
            team=self.team,
            user=self.participant,
            email=self.participant.email,
            full_name='Files Captain',
        )
        TournamentFile.objects.create(
            tournament=self.tournament,
            uploaded_by=self.organizer,
            title='Rules',
            file_type='rules',
            file=ContentFile(b'Demo rules', name='rules.txt'),
        )

    def test_admin_and_registered_participant_can_read_tournament_files(self):
        for user in (self.admin, self.participant):
            self.client.force_authenticate(user=user)
            response = self.client.get(f'/api/tournaments/{self.tournament.id}/files/')

            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data), 1)
            self.assertEqual(response.data[0]['title'], 'Rules')

    def test_approved_jury_can_read_tournament_files(self):
        JuryTournamentRegistration.objects.create(
            jury=self.jury,
            tournament=self.tournament,
            status=JuryRegistrationStatus.APPROVED,
            reviewed_by=self.admin,
            reviewed_at=timezone.now(),
        )

        self.client.force_authenticate(user=self.jury)
        response = self.client.get(f'/api/tournaments/{self.tournament.id}/files/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_unregistered_participant_and_unapproved_jury_are_forbidden(self):
        for user in (self.outsider, self.jury):
            self.client.force_authenticate(user=user)
            response = self.client.get(f'/api/tournaments/{self.tournament.id}/files/')

            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
